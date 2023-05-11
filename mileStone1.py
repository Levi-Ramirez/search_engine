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

'''
1. loop DEV folder and open each file
2. get the html content of json file
3. populate inverted_index dictionary
4. create report

'''


def get_file_text_content(fileName):
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
