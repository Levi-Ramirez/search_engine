from bs4 import BeautifulSoup
import shelve
import json
from nltk.stem import PorterStemmer # to stem
import psutil                       # for RAM usage check 
import math                         # for log when calculating tfidf
import os                           # for files (get size, file paths)

# This is file will create our inverted index
# 0) fetch the document, open file
# 1) tokenize the document
# 2) create postings (go thru token list, generate docID, get word positions, count words up for wordFreq)
# 3) put it all into inverted index (key = term/token, value = list of postings)


class Posting:
  def __init__(self, docID):
    self.docId = docID                  # number documents from 1-n
    self.df = 0                         # first store document frequency (later used for tfidf calculation)
    self.tfidf = 0                      # term frequency * inverse document frequency = (1 + log(tf)) * log(N / df)
    self.position_lst = list()          # set containing all positions that the term exists in document
    #self.fields = fields               # corresponding extent list piece (one for title, for bold, etc)
  
  def add(self, cur_word_pos):
    self.tfidf += 1
    self.position_lst.append(cur_word_pos)

  def getStr(self):
    return (f"docID: {self.docId}, positions: {self.position_lst}\n.")
    
class InvertedIndex:
  def __init__(self):
    self.invertedIndex = dict()  # dictionary of lists (key: terms, value: list of postings for each term)
    self.docID_to_url = dict()
    self.term_to_df = dict()
    self.ps = PorterStemmer()
    self.docCount = 0            # how many documents in corpus? aka N
  

  def get_json_file_paths(self, root_dir):
    json_paths = []
    for cur_dir, all_dirs, all_files in os.walk(root_dir):     # os.walk() traverses a directory tree using DFS, iterating over all files and directories in it
      for f in all_files:
        if f.endswith(".json"):
          json_paths.append(os.path.join(cur_dir, f))
    self.docCount = len(json_paths)
    return json_paths[0:100]

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
        soup = BeautifulSoup(html_content, 'html.parser')
        soup.prettify()  # fix broken HTML
        page_text_content = soup.get_text()

      # get tokens from text content
      tokens = []
      cur_word = ""
      for ch in page_text_content: # read line character by character
        if ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.-'":
          if ch in ".-'":
            continue
          cur_word += ch.lower()  # convert that ch to lower case and add it to the cur_word
        elif len(cur_word) > 0:
          tokens.append(self.ps.stem(cur_word))
          cur_word = ""
      
      tokens.append(self.ps.stem(cur_word))         # last word unadded
      return tokens
    
    except (IOError, json.JSONDecodeError) as e:
      print("Error while processing JSON file")
      return []


  def create_postings(self, docID, tokens):
    # create dictionary of key = token/term, value = list of [word_freq, positions_set]
    # Note: THIS IS FOR ONE DOCUMENT
    dict_term_to_posting = dict()
    for cur_word_pos, t in enumerate(tokens):                # go thru list of tokens
      if t not in dict_term_to_posting:
        dict_term_to_posting[t] = Posting(docID)

      dict_term_to_posting[t].add(cur_word_pos)              # unconditionally add() (word_freq++ and add another cur_word_pos to list)

    # at this point, tfidf is only tf (term frequency), we need to calculate idf and multiply tf * idf, then store it back
    for t in dict_term_to_posting:
      cur_tf = dict_term_to_posting[t].tfidf
      dict_term_to_posting[t].tfidf = (1 + math.log(cur_tf)) * math.log(self.docCount / )
    return dict_term_to_posting


  def create_and_store_InvertedIndex(self, root_dir, store_shelve_file_path):
    json_file_paths = self.get_json_file_paths(root_dir)
    
    # open shelve file, put terms + their postings inside
    with shelve.open(store_shelve_file_path) as my_shelve:
      try:
        for docID, f in enumerate(json_file_paths):
          # if RAM usage exceeds 50%
          # save the current shelve file, call create_and_store_InvertedIndex() again with new info (change to be non-recursive)
          #   total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines().split()[1:])
          #   if round((used_memory/total_memory) * 100, 2) >= 50: 
          #     my_shelve.sync()
          #     my_shelve.close()
          #     create_and_store_InvertedIndex(self, f, new_shelve_path)     # f is current_root_directory
          tokens = self.tokenizer(f)
          dict_term_to_posting = self.create_postings(docID, tokens)     # returns dictionary (key = term, value = a singular posting for the term)
          
          # very slow, pulls entire list from shelve file each time
          for t in dict_term_to_posting:
            if t in my_shelve:
              my_temp_list = my_shelve[t]
            else:
              my_temp_list = list()
            my_temp_list.append(dict_term_to_posting[t])
            my_shelve[t] = my_temp_list

        #self.docCount = docID + 1          # docID starts at 0
      except Exception as e:
          print(f"Error message: {str(e)}")


def generate_report(inverted_index_shelve_file, num_docs):
  fname = "REPORT.txt"
  fname2 = "InvertedIndex.txt"    # store it in a human readable format (not shelve file)

  if os.path.isfile(fname):
    os.remove(fname)
  if os.path.isfile(fname2):
    os.remove(fname2)
  
  with shelve.open(inverted_index_shelve_file) as my_shelve:
    with open(fname, 'w') as f:
      f.write("REPORT: \n")
      f.write("Number of indexed documents: " + str(num_docs) + ". \n")
      f.write("Number of unique words: " + str(len(my_shelve) - 1) + ". \n")         # -1 bc i store "num_unique_words"
      
      file_size = os.path.getsize("analyst.shelve")                                  # get size of text file
      f.write(f"Size of the inverted index: {file_size / 1024.0:.2f} KB.\n")

    with open(fname2, 'w') as f2:
      # put shelve file of inverted_index info into text file
      for term, term_posting_list in my_shelve.items():
        f2.write(f"{term}\n")
        for posting in term_posting_list:
          f2.write(f"{posting.docId}, {posting.tfidf}, {posting.position_lst}\n")
        f2.write("\n")
      

def main():
  shelve_file = "analyst.shelve"
  root_dir = "/home/czejda/cs121hw3/search_engine/ANALYST"
  ii = InvertedIndex()
  ii.create_and_store_InvertedIndex(root_dir, shelve_file)
  generate_report(shelve_file, ii.docCount)

if __name__ == "__main__":
  main()
        





    
