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
    def __init__(self, docID, tfidf):
        self.docId = docID
        self.tfidf = tfidf       # word frequency


def tokenizer(page_text_content):
    '''this function gets text content of a site and tokenzie it. '''
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
    except Exception as e:
        print(f"Error tokenizer: {str(e)}")
        return []
    # stemmed_tokens = [stemmer.stem(token) for token in tokens]

    return tokens


def get_file_text_content(file_path):
    '''this function retuns the text content of a json file'''

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            html_content = data['content']
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            return text_content if text_content else None
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None


def map_docID_url(file_path, docID):
    '''this function maps docID to its URL'''
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            url = data['url']
            docID_urls[docID] = url
    except Exception as e:
        print(f"Error Mappign DocID to URL {file_path}, {docID} : {str(e)}")


def get_file_paths(folder_path):
    '''this function gives a list of paths of all the json files'''
    paths = []
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.endswith('.json'):
                file_path = os.path.join(dirpath, filename)
                paths.append(file_path)
    return paths


inverted_index = {}
docID_urls = {}


def generate_inverted_index(count_tokens, docID):
    '''this function generates/fills the inverted_index. Gets count_tokes and docID as parameters.'''

    try:
        for token in count_tokens:
            tfidf = round(count_tokens[token] / len(count_tokens), 4)
            post = Posting(docID, tfidf)
            if token in inverted_index:
                inverted_index[token].append(post)
            else:
                inverted_index[token] = [post]
    except Exception as e:
        print(f"Error Generating Inverted Index {docID} : {str(e)}")


def token_counter(tokens):
    '''this funciton returns a dictionary of words as keys and number of occurences of those words as values'''
    token_count = {}
    for token in tokens:
        if not token:
            continue
        if token in token_count:
            token_count[token] += 1
        else:
            token_count[token] = 1

    return token_count


def generate_report():
    '''This funciton generates our report for milestone 1. It will print the word and the list of all the documents that word seen and frequency of that word in that doc. for example, "random_word": [(1, 0.24) (99, 0.0029) ... ] where every tupple is (docID, frequency)'''
    try:
        filename = 'REPORT.txt'

        if os.path.isfile(filename):
            os.remove(filename)

        file = open(filename, 'w')
        file.write("REPORT: \n")

        for token in inverted_index:
            file.write(token + ": [ \n")
            new_line_count = 0
            for post in inverted_index[token]:
                file.write("(" + str(post.docId) +
                           ", " + str(post.tfidf) + ') ')
                new_line_count += 1
                if new_line_count >= 10:
                    file.write('\n')
                    new_line_count = 0

            file.write('] \n------------------------------\n')

        file.close()
        print('DONE')
    except Exception as e:
        print(
            f"Error Generating Report: {str(e)}")


def launch_milestone_1():
    '''our main funciton.'''
    folder_path = '/home/mnadi/121/A3/search_engine/DEV'
    paths = get_file_paths(folder_path)  # list of paths to all the files
    docID = 0
    for path in paths:
        if docID >= 1000:
            break
        docID += 1
        # text_content of file located at path
        text_content = get_file_text_content(path)
        if not text_content:  # skip if no text content
            continue
        # assign docID to its proper URL // {docID : url}
        map_docID_url(path, docID)
        tokens = tokenizer(text_content)  # tokenize the text content
        token_count = token_counter(tokens)  # count tokens
        # fill/generate inverted index
        generate_inverted_index(token_count, docID)
    generate_report()


launch_milestone_1()
