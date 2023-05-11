import re
import json
import os
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


'''
1. loop DEV folder and open each file
2. get the html content of json file
3. populate inverted_index dictionary
4. create report

'''


class Posting:
    def __init__(self, docID, tfidf, position_list):
        self.docId = docID
        self.tfidf = tfidf       # word frequency


def tokenizer(page_text_content):
    ''' 
    tokenizer: Takes the page_text_content returned by BeautifulSoup (as a string) and parses this text into tokens.
    - Tokens are a list of strings who's length that is greater than 1.
    '''
    try:
        tokens = []
        cur_word = ""
        stemmer = PorterStemmer()
        for ch in page_text_content:  # read line character by character
            # pig's --> pigs is this a problem?
            # check if character is in english alphabet or a number
            if ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.-'":
                if ch in ".-'":
                    continue
                cur_word += ch.lower()  # convert that ch to lower case and add it to the cur_word
            elif len(cur_word) > 0:
                tokens.append(stemmer.stem(cur_word))
                cur_word = ""
    except:
        print('error in tokenizer')
        return []
    # stemmed_tokens = [stemmer.stem(token) for token in tokens]

    return tokens


def get_file_text_content(file_path):
    '''
    Assuming i get a valid filename to open.
    '''
    '''
    soup_and_soupText: gets the html content from the response and returns the soup object & the page text content
    '''
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            html_content = data['content']
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            return text_content if text_content else None
    except Exception as e:
        print('Error:', e)
        return None


def get_file_paths(folder_path):

    paths = []
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(dirpath, filename)
                paths.append(file_path)
                # print(filename)
    return paths


inverted_index = {}


def generate_inverted_index(tokens):
    
    try:
        for token in tokens:
            if token in inverted_index:
                

def launch_milestone_1():
    folder_path = '/home/mnadi/121/A3/search_engine/DEV'
    paths = get_file_paths(folder_path)
    n = 0

    for path in paths:
        text_content = get_file_text_content(path)
        if not text_content:
            continue
        tokens = tokenizer(text_content)
        
        


launch_milestone_1()
