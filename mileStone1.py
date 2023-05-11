from bs4 import BeautifulSoup
import shelve
import json
from simhash import Simhash
from nltk.stem import PorterStemmer # to stem
from nltk.tokenize import sent_tokenize, word_tokenize

# This is file will create our inverted index
# 0) fetch the document, open file
# 1) tokenize the document
# 2) create postings (go thru token list, generate docID, get word positions, count words up for wordFreq)
# 3) put it all into inverted index (key = term/token, value = list of postings)


class Posting:
  def __init__(self, docID, tfidf, position_list, fields):
    self.docId = docID       # number documents from 1-n
    self.tfidf = tfidf       # word frequency count
    self.position_list
    self.fields = fields     # corresponding extent list piece (one for title, for bold, etc)
    
class InvertedIndex:
  def __init__(self):
    self.invertedIndex = dict()  # dictionary of lists (key: terms, value: postings for each term)
    self.ps = PorterStemmer()
  
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

  def createInvertedIndex():
    pass




# create inverted index
def addInvIndex(textContent, url):
    urlID = urlID(url) #get url ID
    for token in textContent:
      if token in invInd: # it is a token in the dictionary
        if urlID in invInd[token]: 
          invInd[token][urlID] += 1 #if urlID is in invInd[token], increment its counter
        else:
          invInd[token][urlID] = 1 #if urlID is not invInd[token], add it and set it's val to 1
      else: #token is not in the dictionary
        invInd[token] = {urlID : 1} #ex: "hello" = {1904984, 1}



def main():
  pass

if __name__ == "__main__":
  main()
        





    
