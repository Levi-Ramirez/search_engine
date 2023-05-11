import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import validators
from urllib import robotparser
import shelve
from urllib.parse import urljoin
import hashlib
from simhash import Simhash
from nltk.stem import PorterStemmer # to stem
from nltk.tokenize import sent_tokenize, word_tokenize

invInd = {} #dictionary of dictionaries

# tokenizer taken from last assingment
# NEED TO CHANGE FOR THIS ASSIGNMENT'S REQUIREMNTS: ex: U.S.A --> USA (plus more fixes)
# Don't need to remove stop words
# cases: apostraphies, hyphens, periods, 
# becareful of periods at the end of sentences
# Need to stem the words before adding them to tokens (ex: swam --> swim, swimming --> swim), use PorterStemmer
def tokenizer(page_text_content):
    ''' 
    tokenizer: Takes the page_text_content returned by BeautifulSoup (as a string) and parses this text into tokens.
    - Tokens are a list of strings who's length that is greater than 1.
    '''
    tokens = []
    prevchar = ""
    nextChar = ""
    cur_word = ""
    stemmer = PorterStemmer()
    for ch in page_text_content: #read line character by character
# pig's --> pigs is this a problem?
        if ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.-'": #check if character is in english alphabet or a number
            if ch in ".-'":
               continue
            cur_word += ch.lower() #convert that ch to lower case and add it to the cur_word
        elif len(cur_word) > 0:
            tokens.append(stemmer.stem(cur_word))
            cur_word = ""
    
    #stemmed_tokens = [stemmer.stem(token) for token in tokens]
       
    return stemmed_tokens


# open the .json file and read the HTML: Mehmet, do this, (libraries: BeautifulSoup, json), I'm thinking return the text content
# also, we will have to figure out how to deal with broken HTML (BeautifulSoup might handle it)
#def openFileURL(fileName):



def urlID(url):
    return hash(url) #not 100% sure this works

# colin, if you can plz address my comments below. we can discuss them later
def addInvIndex(textContent, url):
    urlID = urlID(url) #get url ID
    #is adding it to a dictionary already placing the URL in sorted order?
    for token in textContent:
      if token in invInd: # it is a token in the dictionary
        #would a dictionary make sense here, or would a list make more sense?
        #my only concern is that would a dictionary place it in sorted order?
        if urlID in invInd[token]: 
          invInd[token][urlID] += 1 #if urlID is in invInd[token], incriment its counter
        else:
          invInd[token][urlID] = 1 #if urlID is not invInd[token], add it and set it's val to 1
      else: #token is not in the dictionary
        invInd[token] = {urlID : 1} #ex: "hello" = {1904984, 1}
        





    
