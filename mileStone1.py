from bs4 import BeautifulSoup
import shelve
import json
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import psutil                       # for RAM usage check 
import math                         # for log when calculating tfidf
import os                           # for files (get size, file paths)
import time

# This is file will create our inverted index
# 0) fetch the document, open file
# 1) tokenize the document
# 2) create postings (go thru token list, generate docID, get word positions, count words up for wordFreq)
# 3) put it all into inverted index (key = term/token, value = list of postings)


class Posting:                          # one per term per document 
  def __init__(self, docID):
    self.docId = docID                  # number documents from 1-n
    self.tfidf = 0                      # use later, after all tfs and df's have been found: term frequency * inverse document frequency = (1 + log(tf)) * log(N / df)
    self.tf = 0                         # term freq (per document)
    self.position_lst = list()          # set containing all positions that the term exists in document
    #self.fields = fields               # corresponding extent list piece (one for title, for bold, etc)
  
  def add(self, cur_word_pos):
    self.tf += 1
    self.position_lst.append(cur_word_pos)

  def getStr(self):
    return (f"docID: {self.docId}, positions: {self.position_lst}\n.")
  
  def calc_tfidf(self, N, df):
    # (1 + log(tf)) * log(N / df)
    # tf = term freq in current document (aka len(self.position_lst))
    # N = total documents (everything)
    # df = document frequency (how many documents across N the term shows up)
    return (1 + math.log(len(self.position_lst))) * math.log(N / df)
    
class InvertedIndex:
  def __init__(self):
    self.invertedIndex = dict()      # dict of lists, key: terms, val: list of postings for each term
    self.docID_to_url = dict()       # dict, key: docID, val: url string (actually, json filepath here for DEV and ANALYST folders)
    #self.term_to_df = dict()         # dict, key: term, val: document frequency integer
    self.ps = PorterStemmer()
    self.docCount = 0            # how many documents in corpus? aka N
    self.num_indexes = 0

  def get_json_file_paths(self, root_dir):
    json_paths = []
    for cur_dir, all_dirs, all_files in os.walk(root_dir):     # os.walk() traverses a directory tree using DFS, iterating over all files and directories in it
      for f in all_files:
        if f.endswith(".json"):
          json_paths.append(os.path.join(cur_dir, f))
    self.docCount = len(json_paths)
    return json_paths[:200]

  def is_json_file_size_within_ram_limit(self, file_path):
    file_size_in_bytes = os.path.getsize(file_path)
    ram_size_in_bytes = psutil.virtual_memory().total
    ram_limit_in_bytes = 0.75 * ram_size_in_bytes

    return file_size_in_bytes <= ram_limit_in_bytes

  def tokenizer(self, json_file_path):
    try:
      if self.is_json_file_size_within_ram_limit(json_file_path):
        # load the json file, each json file has: URL, Content, Encoding (ascii or utf-8)
        with open(json_file_path, 'r') as f:
          json_data = json.load(f)     # read contents of file and converts it into a python dict or lists
      
        # use BS4 to get text content
        html_content = json_data["content"]
        url = json_data["url"]
        soup = BeautifulSoup(html_content, 'html.parser')
        soup.prettify()  # fix broken HTML
        page_text_content = soup.get_text()

      # get tokens from text content
      tokens = word_tokenize(page_text_content)
      stemmed_tokens = [self.ps.stem(token.lower()) for token in tokens if token.isalnum()]
      
      return stemmed_tokens, url 
    
    except (IOError, json.JSONDecodeError) as e:
      print("Error while processing JSON file")
      return []


  def create_postings(self, docID, tokens):
    # create dictionary of key = term, value = list of [word_freq, positions_set]
    # Note: THIS IS FOR ONE DOCUMENT (but all terms within)
    dict_term_to_posting = dict()
    for cur_word_pos, t in enumerate(tokens):                # go thru list of tokens
      if t not in dict_term_to_posting:
        dict_term_to_posting[t] = Posting(docID)

      dict_term_to_posting[t].add(cur_word_pos)              # unconditionally add() (term_freq++ and add another cur_word_pos to position list)

    return dict_term_to_posting


  def create_and_store_InvertedIndex(self, root_dir, store_shelve_file_path):
    json_file_paths = self.get_json_file_paths(root_dir)
    
    # open shelve file, put terms + their postings inside
    #with shelve.open(store_shelve_file_path, writeback=True) as my_shelve:
    if True:
      my_shelve_dict = dict()
      start_time = time.time()
      last_ts = time.time()
      for docID, f in enumerate(json_file_paths):
        if docID % 100 == 1:
          ts = time.time()
          print(f"d_id: {docID}, time for last 100: {ts - last_ts}, avg time per query: {(ts - start_time) / docID}", flush=True)
          #print()
          last_ts = ts
        tokens, url = self.tokenizer(f)
        self.docID_to_url[docID] = url          # keep track of which docID corresponds to which url
        dict_term_to_posting = self.create_postings(docID, tokens)     # returns dictionary (key = term, value = a singular posting for the term)
        
        # update document frequency (in self.term_to_df)
        # terms_added_to_df = set()          # set of terms that tracks if it's been added to self.term_to_df
        for t, posting in dict_term_to_posting.items():
        #   if t not in terms_added_to_df:
        #     if t not in self.term_to_df:
        #       self.term_to_df[t] = 0
        #     self.term_to_df[t] += 1
        #     terms_added_to_df.add(t)

          # put postings to shelve file
          # VERY SLOW, pulls entire list from shelve file each time, modifies it, then stores it back
          if t not in my_shelve_dict:
            my_shelve_dict[t] = list()
          my_shelve_dict[t].append(posting)
          
            # new_index = "shelve_index" + str(self.num_indexes) + ".shelve"
            # self.num_indexes += 1
        with shelve.open("analyst.shelve") as my_shelve:
          my_shelve["my_shelve_dict"] = my_shelve_dict
          my_shelve["num_documents"] = self.docCount
          my_shelve["docID_to_URL"] = self.docID_to_url



def generate_report(inverted_index_shelve_file, num_docs):
  fname = "REPORT.txt"
  fname2 = "InvertedIndex.txt"    # store it in a human readable format (not shelve file)

  if os.path.isfile(fname):
    os.remove(fname)
  if os.path.isfile(fname2):
    os.remove(fname2)
  
  with shelve.open(inverted_index_shelve_file, writeback=True) as my_shelve:
    with open(fname, 'w') as f:
      f.write("REPORT: \n")
      f.write("Number of indexed documents: " + str(num_docs) + ". \n")
      f.write("Number of unique words: " + str(len(my_shelve["my_shelve_dict"]) - 1) + ". \n")         # -1 bc i store "num_unique_words"
      
      file_size = os.path.getsize("analyst.shelve")                                  # get size of text file
      f.write(f"Size of the inverted index: {file_size / 1024.0:.2f} KB.\n")

    with open(fname2, 'w') as f2:
      # put shelve file of inverted_index info into text file
      for term, term_posting_list in my_shelve["my_shelve_dict"].items():
        f2.write(f"{term}\n")
        for posting in term_posting_list:
          f2.write(f"{posting.docId}, {posting.tf}, {posting.position_lst}\n")
        f2.write("\n")
      

def main():
  shelve_file = "analyst.shelve"
  root_dir = "/home/czejda/cs121hw3/search_engine/ANALYST"
  ii = InvertedIndex()
  ii.create_and_store_InvertedIndex(root_dir, shelve_file)
  #generate_report(shelve_file, ii.docCount)

if __name__ == "__main__":
  main()
        





    
