from mileStone1 import Posting
import shelve
import time
from nltk.stem import PorterStemmer
import heapq

class Timer:
    def __init__(self):
        self.cur_ts = time.time()
    
    def print_ts(self, label = "Time diff is"):
        now_ts = time.time()
        print(f"{label}: {now_ts - self.cur_ts}")
        self.cur_ts = now_ts

class Search:
    def __init__(self, index_shelve):
        self.index_dict = index_shelve["my_shelve_dict"]              # this is just a dictionary (pulled from shelve file)
        self.num_documents = index_shelve["num_documents"]
        self.URLs = index_shelve["docID_to_URL"]
        self.ps = PorterStemmer()

    def process_query(self, query_string):    # perform filtering
        return [self.ps.stem(term) for term in query_string.split()]

    def calc_ranking(self, docID, postings):
        # sum up the tf-idfs for each query term that shows up in the document
        total_tfidf = 0
        for posting_list in postings:        # for each search term's posting list, one per doc
            for p in posting_list:           # go thru individual posting in list
                if p.docId == docID:             # found the posting with matching docID
                    total_tfidf += p.calc_tfidf(self.num_documents, len(posting_list))

        #print(f"tfidf: {total_tfidf} for docID {docID}.")
        return total_tfidf

    def calc_top_n(self, n, postings):     # postings is a list of lists (of posting objects, dif terms)
        t = Timer()
        # find the top n entries using a list of postings
        #posting_list = [p for p in posting_list for posting_list in postings]             # get every posting object 
        document_sets = [{p.docId for p in posting_list} for posting_list in postings]    # gives list of sets of document IDs for
        #t.print_ts("Calc_top_n time diff 1")
        # now find intersection to find documents that contain each term at least once
        if len(document_sets) == 0 or any(len(doc_set) == 0 for doc_set in document_sets):     # intersection cannot happen if one of the sets is empty
            return []
        
        candidate_docIDs = set.intersection(*document_sets)
        #t.print_ts("Calc_top_n time diff 2")

        #sorted_docIDs = sorted(candidate_docIDs, key = lambda x: -self.calc_ranking(x, postings))        # negative to sort in reverse
        # sort using heap, much more efficient than sorted() function
        heap = []
        for id in candidate_docIDs:
            heap_key = (self.calc_ranking(id, postings), id)
            if len(heap) < n:
                heapq.heappush(heap, heap_key)
            else:
                heapq.heappushpop(heap, heap_key)

        #t.print_ts("Calc_top_n time diff 3")

        #print(f"Num documents found: {len(sorted_docIDs)}")

        return heapq.nlargest(n, heap)     # gives the tuples

    def search_for(self, query_string, n):
        query = self.process_query(query_string)
        postings = [self.index_dict.get(t, list()) for t in query]    # .get() is safe, list of lists of postings
        return self.calc_top_n(n, postings)
    
def main():
    #query = "nearli"
    index_shelve_file = "dev.shelve"
    
    
    with shelve.open(index_shelve_file, 'r') as my_shelve:    # open index shelve
        
        s = Search(my_shelve)
        while True:
            user_query = input("Search for: ")
            start_t = time.time()

            top_5_tuples = s.search_for(user_query, 5)       # list of tuples, (tfidf, docID)
            print("Your top 5 results are:")
            for tfidf, docID in top_5_tuples:
                print(f"DocID: {docID}, Tfidf: {tfidf}, URL: {s.URLs[docID]}")
            print(f"Total time was {time.time() - start_t}\n")

if __name__ == "__main__":
    main()