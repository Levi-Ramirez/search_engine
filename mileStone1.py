import re
import json

from urllib.parse import urlparse
from bs4 import BeautifulSoup
import validators
from urllib import robotparser
import shelve
from urllib.parse import urljoin
import hashlib
from simhash import Simhash
from nltk.stem import PorterStemmer  # to stem
from nltk.tokenize import sent_tokenize, word_tokenize
from stop_words import get_stop_words

invInd = {}  # dictionary of dictionaries

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


def open_file_url(fileName):
    '''
    Assuming i get a valid filename to open.
    '''
    '''
    soup_and_soupText: gets the html content from the response and returns the soup object & the page text content
    '''
    try:
        with open(fileName, 'r') as f:
            data = json.load(f)
            html_content = data['content']
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            return text_content if text_content else None
    except Exception as e:
        print('Error:', e)
        return None


test1 = open_file_url(
    '/home/mnadi/121/A3/search_engine/DEV/aiclub_ics_uci_edu/8ef6d99d9f9264fc84514cdd2e680d35843785310331e1db4bbd06dd2b8eda9b.json')

print('8ef6d99d9f9264fc84514cdd2e680d35843785310331e1db4bbd06dd2b8eda9b.json: ', test1)
test5 = open_file_url(
    '/home/mnadi/121/A3/search_engine/DEV/aiclub_ics_uci_edu/brokenHTML.json')

print('brokenHTML.json returns: ', test5)

test2 = open_file_url(
    'this file does not exit')
print('FILE DOES NOT EXIST returns: ', test2)

test3 = open_file_url(
    '/home/mnadi/121/A3/search_engine/DEV/aiclub_ics_uci_edu/noContent.json')

print('noContent.json returns: ', test3)

test4 = open_file_url(
    '/home/mnadi/121/A3/search_engine/DEV/aiclub_ics_uci_edu/emptyContent.json')

print('emptyContent.json returns: ', test4)


def url_id(url):
    return hash(url)  # not 100% sure this works

# colin, if you can plz address my comments below. we can discuss them later


def add_inv_index(textContent, url):
    urlID = urlID(url)  # get url ID
    # is adding it to a dictionary already placing the URL in sorted order?
    for token in textContent:
        if token in invInd:  # it is a token in the dictionary
            # would a dictionary make sense here, or would a list make more sense?
            # my only concern is that would a dictionary place it in sorted order?
            if urlID in invInd[token]:
                # if urlID is in invInd[token], incriment its counter
                invInd[token][urlID] += 1
            else:
                # if urlID is not invInd[token], add it and set it's val to 1
                invInd[token][urlID] = 1
        else:  # token is not in the dictionary
            invInd[token] = {urlID: 1}  # ex: "hello" = {1904984, 1}


# for all files: (need to find out how to loop through all of the files and pass them to open_file_url(fileName))
#  1. retrieve file & assign ID (aka docID)
#  2. tokenize file
#  3. pass docID and tokenized text to add_inv_index


