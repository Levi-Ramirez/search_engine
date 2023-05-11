from bs4 import BeautifulSoup
import shelve
import json
from simhash import Simhash
from nltk.stem import PorterStemmer # to stem
from nltk.tokenize import sent_tokenize, word_tokenize
import psutil

# This is file will create our inverted index
# 0) fetch the document, open file
# 1) tokenize the document
# 2) create postings (go thru token list, generate docID, get word positions, count words up for wordFreq)
# 3) put it all into inverted index (key = term/token, value = list of postings)


class Posting:
  def __init__(self, docID, tfidf, position_list):
    self.docId = docID       # number documents from 1-n
    self.tfidf = tfidf       # word frequency count
    self.position_set        # set containing all positions that the term exists in document
    #self.fields = fields    # corresponding extent list piece (one for title, for bold, etc)
    

class InvertedIndex:
  def __init__(self):
    self.invertedIndex = dict()  # dictionary of lists (key: terms, value: postings for each term)
    self.ps = PorterStemmer()
  

  def get_json_file_paths(root_dir):
    json_paths = []
    for cur_dir, all_dirs, all_files in os.walk(root_dir):     # os.walk() traverses a directory tree using DFS, iterating over all files and directories in it
      for f in all_files:
        if f.endswith(".json"):
          json_paths.append(os.path.join(cur_dir, f))


  def tokenizer(self, json_file_path):
    try:
      # load the json file, each json file has: URL, Content, Encoding (ascii or utf-8)
      with open(json_file_path) as f:
        json_data = json.load(f)     # read contents of file and converts it into a python dict or list

      # check if json file has html data for us to tokenize
      for key, val in json_data.items():
        if isinstance(val, str) and "<html" in val.lower():
          has_html_data = True
        else:
          return []
      
      # use BS4 to get text content
      soup = BeautifulSoup(json["content"], "html.parser")
      soup.prettify()  # fix broken HTML
      page_text_content = soup.get_text()

      # get tokens from text content
      tokens = []
      cur_word = ""
      for ch in page_text_content: # read line character by character
          if ch in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890': #check if character is in english alphabet or a number
              cur_word += ch.lower() # convert that ch to lower case and add it to the cur_word
          else:
              stemmed_word = self.ps.stem(cur_word)
              tokens.append(stemmed_word) # found space, add cur word to token list 
              cur_word = ""               # reset cur_word
      
      tokens.append(cur_word)         # last word unadded
      return tokens
    
    except (IOError, json.JSONDecodeError) as e:
      print("Error while processing JSON file")
      return []


  def create_postings(self, docID, tokens):
    # create dictionary of key = token/term, value = tuple of (word_freq, positions_set)
    cur_word_pos = 0
    temp_dict = {}
    for t in tokens:
      if t not in temp_dict:
        pos_set = set()
        pos_set.add(cur_word_pos)
        temp_dict[t] = (1, pos_set)         # word_freq, positions_set
      else:
        temp_dict[t][0] += 1                # update word_freq
        temp_dict[t][1].add(cur_word_pos)   # update pos_set
      cur_word_pos += 1
    
    # develop postings objects using temp_dict (very inefficient i think lol, wrote this at 2 am)
    dict_term_to_posting = []
    for term in temp_dict:
      posting = Posting(docID, temp_dict[term][0], temp_dict[term][1])
      dict_term_to_posting[term] = posting

    return dict_term_to_posting


  def create_and_store_InvertedIndex(self, root_dir, store_shelve_file_path):
    json_file_paths = self.get_json_file_paths(root_dir)
    
    # open shelve file, put terms + their postings inside
    with shelve.open(store_shelve_file_path) as my_shelve:
      docID = 0
      for f in json_file_paths:
        tokens = self.tokenize(f)
        dict_term_to_posting = self.create_postings(docID, tokens)
        
        for t in tokens:
          if t in my_shelf:
            my_shelve[t].add(dict_term_to_posting[t])
          else:
            postings_set = set()
            postings_set.add(dict_term_to_posting[t])
            my_shelve[t] = postings_set
        docID += 1


def main():
  root_dir = ""
  ii = InvertedIndex()
  ii.create_and_store_InvertedIndex(root_dir)

if __name__ == "__main__":
  main()
        





    
