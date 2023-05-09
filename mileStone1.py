import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import validators
from urllib import robotparser
import shelve
from urllib.parse import urljoin
import hashlib
from simhash import Simhash
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

# tokenizer taken from last assingment
# NEED TO CHANGE FOR THIS ASSIGNMENT'S REQUIREMNTS: ex: U.S.A --> USA (plus more fixes)
def tokenizer(page_text_content):
    ''' 
    tokenizer: Takes the page_text_content returned by BeautifulSoup (as a string) and parses this text into tokens.
    - Tokens are a list of strings who's length that is greater than 1.
    '''
    tokens = []
    
    cur_word = ""
    for ch in page_text_content: #read line character by character
        if ch in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890': #check if character is in english alphabet or a number
            cur_word += ch.lower() #convert that ch to lower case and add it to the cur_word
        elif cur_word in stop_words:
            cur_word = ""
        # if it is not a stop_word && is not alphanumeric && the length is greater than one, then we can append it to the list
        elif len(cur_word) > 1: #we do not want single charecters. for example James's would give us "James" and "s" if we dont do this 
            tokens.append(cur_word) # add cur word to token list 
            cur_word = "" #reset cur_word
        else:
            cur_word = ''
    
    # if cur_word is not empty, we need to add it to the list bc we do not wanna skip the last word unadded
    if len(cur_word) > 1 and cur_word not in stop_words: 
        tokens.append(cur_word)
    return tokens


