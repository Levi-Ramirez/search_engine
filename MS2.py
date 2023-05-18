import mileStone1
import shelve


class Search:
    def __init__(self, index_shelve):
        self.index_shelve = index_shelve      # already opened in main

    def process_query(self, query_string):    # perform filtering
        return query_string.split()

    def calc_ranking(self, docID):
        # sum up the tf-idfs for each query term that shows up in the document
        return 0

    def calc_top_n(self, n, postings):     # postings is a list of lists (of posting objects, dif terms)
        # find the top n entries using a list of postings
        posting_list = [p for p in posting_list for posting_list in postings]             # get every posting object 
        document_sets = [{p.docId for p in posting_list} for posting_list in postings]    # gives list of sets of document IDs for

        # now find intersection to find documents that contain each term at least once
        candidate_docIDs = set.intersection(*document_sets)
        sorted_docIDs = sorted(candidate_docIDs, key = self.calc_ranking)
        
        return sorted_docIDs[:n]     # get top n

    def search_for(self, query_string):
        query = self.process_query()
        postings = [self.index_shelve.get(t, list()) for t in query]    # .get() is safe, list of lists of postings
        return 0
    
def main():
    query = "hot dog"
    index_shelve_file = "analyst.shelve"
    
    with shelve.open(index_shelve_file) as my_shelve:    # open index shelve
        s = Search(my_shelve)
        s.search_for(query)

if __name__ == "__main__":
    main()