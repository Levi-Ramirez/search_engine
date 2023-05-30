from mileStone1 import Posting
import shelve
import time
from nltk.stem import PorterStemmer
import heapq
import openai
import json
from bs4 import BeautifulSoup

class Timer:
    def __init__(self):
        self.cur_ts = time.time()
    
    def print_ts(self, label = "Time diff is"):
        now_ts = time.time()
        print(f"{label}: {now_ts - self.cur_ts}")
        self.cur_ts = now_ts

class Search:
    def __init__(self):
        self.index_dict = dict()
        with open("index_of_index.txt", "r") as i_of_i:      # big dict of term to byte offset, used for seeking postings list for a term in complete_index.txt
            self.index_dict = json.load(i_of_i)              
        
        self.urls_dict = dict()
        with open("docID_to_url.txt", "r") as dtu:
            self.urls_dict = json.load(dtu)                  # big dict of docID to URL, need to return URLs to user

        self.json_file_paths = list()                        # big list of json file paths (local), used later for GPT prompting
        with open("file_paths.txt", "r") as fps:
            self.json_file_paths = json.load(fps)

        self.num_documents = 55393                           # will sort this out later
        self.ps = PorterStemmer()
        self.stemmed_stop_words = {"that'll", 'from', "you'r", 'o', 'own', 'so', 'have', 'and', 'is', 
                                   'some', 'dure', 'at', 'into', 'with', 'same', "it'", 'doe', 'as', 
                                   'about', "hasn't", 'shouldn', 'too', "mightn't", 'needn', 'between', 
                                   'myself', "isn't", "wasn't", 'hi', 'me', 'can', "wouldn't", "haven't", 
                                   'just', 'not', 'most', "mustn't", "shouldn't", "you'v", 'had', 'am', 
                                   'than', 'off', 'that', 'if', 'where', 'of', 'becaus', 'don', 'further', 
                                   'i', 'whi', 'below', 'what', 'you', 'y', 're', 'to', 'themselv', 
                                   'again', 'when', 'which', 'yourself', 'each', 'on', 'our', "shan't", 
                                   'aren', 'onli', 'until', 'mightn', 's', 'then', 'veri', 'itself', 
                                   'or', 'weren', 'thi', 'such', 'over', 'by', 'up', 'yourselv', 
                                   "doesn't", 'there', 'ha', 'now', 'we', 'him', 'her', 'a', 'himself', 
                                   'my', 'd', 'herself', 'ani', 'after', 'isn', 'ourselv', 'under', 
                                   'your', 'their', 'are', 'for', 'them', 'shan', 'ma', 'onc', 'will', 
                                   'befor', 'she', "you'll", 'ain', 'haven', "weren't", "needn't", 
                                   'an', 'but', "don't", 'while', 'the', 'wouldn', 'doesn', 'll', 
                                   "you'd", 'he', "didn't", "should'v", 've', "hadn't", 'should', 
                                   "couldn't", 'couldn', 'whom', 'didn', 'in', 'been', 'wasn', 'more', 
                                   'm', 'it', 'no', 'few', 'won', 'who', 'both', 't', 'do', 'out', 
                                   'hadn', 'they', "aren't", 'were', 'mustn', 'wa', 'be', 'hasn', 
                                   'here', 'those', "won't", "she'", 'abov', 'against', 'down', 
                                   'nor', 'all', 'through', 'did', 'other', 'these', 'how'}

    def process_query(self, query_string):    # perform filtering
        stemmed_query_words = [self.ps.stem(term.lower()) for term in query_string.split()]
        return [w for w in stemmed_query_words if w not in self.stemmed_stop_words]              # remove stop words from query

    def calc_top_n(self, n, postings):     # postings is a list of lists (of posting objects, dif terms)
        t = Timer()
        # find the top n entries using a list of postings
        document_sets = [{p[0] for p in posting_list} for posting_list in postings]       # gives list of sets of document IDs for
        #t.print_ts("Calc_top_n time diff 1")

        # now find intersection to find documents that contain each term at least once
        if len(document_sets) == 0 or any(len(doc_set) == 0 for doc_set in document_sets):     # intersection cannot happen if one of the sets is empty
            return []
        
        candidate_docIDs = set.intersection(*document_sets)        # find docIDs common to every term
        #t.print_ts("Calc_top_n time diff 2")

        # sort using heap, much more efficient than sorted() function
        doc_id_to_tfidf = dict()         # for this query only (bc we did intersection of documents)
        for posting_list in postings:
            for p in posting_list:
                if p[0] in candidate_docIDs:
                    if p[0] not in doc_id_to_tfidf:      # p[0] is docID
                        doc_id_to_tfidf[p[0]] = 0
                    doc_id_to_tfidf[p[0]] += p[1]        # p[1] is tfidf, we want to sum all tfidf's for each docID

        heap = []
        for id in candidate_docIDs:
            heap_key = (doc_id_to_tfidf[id], id)
            if len(heap) < n:
                heapq.heappush(heap, heap_key)
            else:
                heapq.heappushpop(heap, heap_key)

        #t.print_ts("Calc_top_n time diff 3")

        #print(f"Num documents found: {len(sorted_docIDs)}")

        return heapq.nlargest(n, heap)     # gives the tuples

    def search_for(self, query_string, n):
        query = self.process_query(query_string)
        byte_offsets = [self.index_dict.get(t, -1) for t in query]    # if term in dict, give byte offset for where to find in complete_index.txt
        all_postings_list = list()                                    # list of lists
        with open("complete_index.txt", "r") as ci:
            for bo in byte_offsets:
                if bo != -1:                 # if term exists in index
                    ci.seek(bo)
                    term_posting_list = ci.readline()
                    all_postings_list.append(json.loads(term_posting_list))         # add the list object into all_postings_list
        return self.calc_top_n(n, all_postings_list)
    
    def get_text_from_json_file(self, file_path):
        with open(file_path, 'r') as f:
          json_data = json.load(f)     # read contents of file and converts it into a python dict or lists
      
        # use BS4 to get text content
        html_content = json_data["content"]
        soup = BeautifulSoup(html_content, 'html.parser')
        soup.prettify()  # fix broken HTML
        page_text_content = soup.get_text()
        return page_text_content
    
    def get_gpt_title_and_summary(self, docID):
        openai.api_key = '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'
        file_path = self.json_file_paths[docID]
        doc_text = self.get_text_from_json_file(file_path)

        messages_title = [  {"role": "system", "content": "give a brief title for this text: " + doc_text}  ]   # may not be necessary
        messages_summary = [  {"role": "system", "content": "give a brief summary for this text: " + doc_text}  ]
        
        title = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages = messages_title)
        summary = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages = messages_summary)
        return title, summary
        
def main():
    s = Search()
    while True:
        user_query = input("Search for: ")
        start_t = time.time()

        top_5_tuples = s.search_for(user_query, 5)       # list of tuples, (tfidf, docID)

        # old version
        # print("Your top 5 results are:")
        # for tfidf, docID in top_5_tuples:
        #     print(f"DocID: {docID}, Tfidf: {tfidf}, URL: {s.urls_dict[str(docID)]}")
        # print(f"Total time was {time.time() - start_t}\n")

        # new version
        print("Your top 5 results are:")
        for tfidf, docID in top_5_tuples:
            title, summary = s.get_gpt_title_and_summary(docID)
            print(f"{s.urls_dict[str(docID)]} \n{title} \n{summary}")   # url, then title, then summary


if __name__ == "__main__":
    main()