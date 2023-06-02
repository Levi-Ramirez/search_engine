import re
import json
import os
import os.path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import validators
from urllib import robotparser
import shelve
from urllib.parse import urljoin
import hashlib
''' the commented out libraries don't import correctly '''
# from porter2stemmer import Porter2Stemmer
# from simhash import Simhash
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer  # to stem
# from nltk.tokenize import sent_tokenize, word_tokenize
from stop_words import get_stop_words
import shelve


'''
1. loop DEV folder and open each file
2. get the html content of json file
3. populate inverted_index dictionary
4. create report

'''
fileCount = 0
indexSplitCounter = 0
docID = 0
inverted_index = {}
docID_urls = {}
index_of_index = {}


# class Posting:
#     def __init__(self, docID, token_locs, tfidf):
#         self.docId = docID
#         self.token_locs = token_locs
#         self.tfidf = tfidf       # word frequency

# instead, lets try to define a list



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
        if len(cur_word) > 1:
            tokens.append(stemmer.stem(cur_word))
        return tokens  
    except Exception as e:
        print(f"Error tokenizer: {str(e)}")
        return []
    # stemmed_tokens = [stemmer.stem(token) for token in tokens]



def get_file_text_content(file_path):
    '''this function returns the text content of a json file'''

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            html_content = data['content']
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            bold_word_counter = {}
            for tag in soup.findAll():
                tag_name = tag.name
                tag_text_content = tag.get_text()
                if tag_name == 'strong' or tag_name == 'h1' or tag_name == 'h2' or tag_name == 'h3': 
                    for word in tokenizer(tag_text_content):
                        if word in bold_word_counter:
                            bold_word_counter[word] += 1
                        else:
                            bold_word_counter[word] = 1
                        
            return (text_content, bold_word_counter) if text_content else (None, bold_word_counter)
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return (None, {})



def read_large_line(file):
    chunk_size = 4096  # python line buffer size
    line = ''

    while True:
        chunk = file.readline(chunk_size)
        line += chunk

        if len(chunk) < chunk_size or '\n' in chunk:
            break

    return line


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


def write_to_file(thisFile, newDict):
    for key in newDict:
        tempDict = {key: newDict[key]}
        json.dump(tempDict, thisFile)
        thisFile.write('\n')


def generate_inverted_index(token_locs, docID, strong_word_count):
    '''this function generates/fills the inverted_index. Gets token_locs (key is a word and value is a list of the postions of that word) and docID as parameters, strong_word_count (dic of strong words and count).'''
    

    global indexSplitCounter
    global fileCount
    indexSplitCounter += 1
    if indexSplitCounter > 5000:
        fileName = "index" + str(fileCount) + ".txt"
        if os.path.exists(fileName):
            os.remove(fileName)
        with open(fileName, "w") as thisFile:
            res = sorted(inverted_index.items())
            newDict = dict(res)
            # json.dump(newDict, thisFile)  REPLACE THIS LINE
            write_to_file(thisFile, newDict)  # replacement

        inverted_index.clear()
        indexSplitCounter = 0
        fileCount += 1
    try:
        for token in token_locs:
            # tfidf = round(count_tokens[token] / len(count_tokens), 4)
            
            tfidf = 0
            
            if token in strong_word_count and strong_word_count[token] > 0:
                tfidf = len(token_locs[token]) + strong_word_count[token]
                strong_word_count[token] -= 1
            else:
                tfidf = len(token_locs[token])
                

            # post = Posting(docID, token_locs[token], tfidf)
            post = [docID, token_locs[token], tfidf]
            if token in inverted_index:
                inverted_index[token].append(post)
            else:
                inverted_index[token] = [post]
    except Exception as e:
        print(f"Error Generating Inverted Index {docID} : {str(e)}")


def write_remaining_index():
    global indexSplitCounter
    global fileCount
    indexSplitCounter += 1

    fileName = "index" + str(fileCount) + ".txt"
    if os.path.exists(fileName):
        os.remove(fileName)
    with open(fileName, "w") as thisFile:
        res = sorted(inverted_index.items())
        newDict = dict(res)
        # json.dump(newDict, thisFile)  REPLACE THIS LINE
        write_to_file(thisFile, newDict)  # replacement

    inverted_index.clear()
    indexSplitCounter = 0
    fileCount += 1


def getKey(myStr):
    firstQuote = myStr.find('"')
    secondQuote = myStr.find('"', firstQuote + 1)
    if firstQuote == -1 or secondQuote == -1:  # if there is no key, return empty string
        return ""
    keyStr = myStr[firstQuote + 1: secondQuote]
    return keyStr


def merge_step(dictHolder, dict2):
    '''
    this merges two given dictionaries (in this case tokens) together from the passed dictionaries
    - technically, there should only be one key per dictionary (see merge_partial_indexes)

    '''
    for key in dict2:
        if key in dictHolder:
            # dictHolder[key].append(dict2[key])
            i = 0
            k = 0
            dict2List = dict2[key]
            # for every posting already in the dictHolder
            for posting in dictHolder[key]:
                if (posting[0] > dict2List[k][0]):
                    # dictHolder[key].insert(i, dictHolder[key].insert(dict2List[k]))
                    dictHolder[key].insert(i, dict2List[k])
                    k = + 1
                    if k >= len(dict2List):  # reached the end
                        break
                i += 1

            while k < len(dict2List):  # if we havent reached the end of dict2List
                dictHolder[key].append(dict2List[k])
                k += 1

        else:
            dictHolder[key] = dict2[key]


def merge_partial_indexes():
    '''Merges the partial indexes'''
    if os.path.isfile("full_index.txt"):
        os.remove("full_index.txt")
    full_index = open("full_index.txt", 'w')
    global fileCount
    tempCount = 0
    arrFiles = []
    while tempCount < fileCount:  # open all files loop
        fileName = "index" + str(tempCount) + ".txt"
        tempHolder = open(fileName, "r")
        arrFiles.append(tempHolder)
        tempCount += 1
    arrNextMinIndexesText = []
    arrNextMinIndexesDict = []
    # while True:
    tempCount = 0
    while tempCount < fileCount:
        # will be a list of dictionary entries represented by text
        tempStr = read_large_line(arrFiles[tempCount])
        
        if tempStr:
            arrNextMinIndexesText.append(tempStr)
            # arrNextMinIndexesText.append(arrFiles[tempCount].readline()) #will be a list of dictionary entries represented by text
            # will be a list of ACTUAL dictionary entries
            arrNextMinIndexesDict.append(
                json.loads(arrNextMinIndexesText[tempCount]))
        tempCount += 1
    # minKey = getKey(arrNextMinIndexesText[0])
    while (True):
        minKey = ""
        for x in arrNextMinIndexesText:  # gets the first non-empty string and assign it to minKey
            if x != "":
                minKey = x
                break
        if minKey == "":  # means that all of them were empty strings, nothing else to read from all files
            break

        for x in arrNextMinIndexesText:
            curKey = getKey(x)
            if curKey != "" and (curKey < minKey):
                minKey = curKey
        # if(minKey == float('inf')):
        #     break
        i = 0
        dictHolder = {}  # holder is the new dictionary which we will write to the file
        # print(arrNextMinIndexesDict)
        # print(minKey)

        while i < fileCount:
            if minKey in arrNextMinIndexesDict[i]:
                # print(arrNextMinIndexesDict[i])
                merge_step(dictHolder, arrNextMinIndexesDict[i])
                # print(dictHolder)
                arrNextMinIndexesText[i] = read_large_line(
                    arrFiles[i])  # update this to the next line
                # arrNextMinIndexesText[i] = arrFiles[i].readline() #update this to the next line
                if (arrNextMinIndexesText[i] != ""):
                    # update this to the next dict entry
                    arrNextMinIndexesDict[i] = json.loads(
                        arrNextMinIndexesText[i])
            i += 1
        # print(dictHolder)
        json.dump(dictHolder, full_index)
        full_index.write('\n')

    tempCount = 0
    while tempCount < fileCount:  # close all files loop
        arrFiles[tempCount].close()
        tempCount += 1
    full_index.close()


def token_locator(tokens):
    '''this function returns a dictionary of words with a list of the indexes where it the word is'''
    token_locs = {}
    i = 0
    for token in tokens:
        if not token:
            continue
        if token in token_locs:
            token_locs[token].append(i)
        else:
            token_locs[token] = [i]
        i += 1

    return token_locs


def generate_report():
    '''This funciton generates our report for milestone 1. It will print the word and the list of all the documents that word seen and frequency of that word in that doc. for example, "random_word": [(1, 0.24) (99, 0.0029) ... ] where every tupple is (docID, frequency)'''
    try:
        filename = 'REPORT.txt'
        file2 = 'InvertedIndex.txt'

        if os.path.isfile(filename):
            os.remove(filename)

        if os.path.isfile(file2):
            os.remove(file2)

        file = open(filename, 'w')
        file.write("REPORT: \n")

        InvertedIndexTXT = open(file2, 'w')

        file.write('Number of indexed documents: ' + str(docID) + '.\n')

        file.write('Number of unique words: ' +
                   str(len(inverted_index)) + '.\n')

        for token in inverted_index:
            InvertedIndexTXT.write(token + ": [ \n")
            new_line_count = 0
            for post in inverted_index[token]:
                # InvertedIndexTXT.write("(" + str(post.docId) +
                #                        ", " + str(post.token_locs) + ', ' + str(post.tfidf) + ') ')
                InvertedIndexTXT.write("(" + str(post[0]) +
                                       ", " + str(post[1]) + ', ' + str(post[2]) + ') ')
                new_line_count += 1
                if new_line_count >= 10:
                    InvertedIndexTXT.write('\n')
                    new_line_count = 0

            InvertedIndexTXT.write('] \n------------------------------\n')


        file_size = os.path.getsize(file2)
        file.write('Size of the inverted index: ' +
                   str(file_size // 1024) + ' KB.\n')
        file.close()
        InvertedIndexTXT.close()
        print('DONE')
    except Exception as e:
        print(
            f"Error Generating Report: {str(e)}")


def create_index_of_index():
    full_index = open("full_index.txt", 'r')
    while True:
        pos = full_index.tell()
        curLine = read_large_line(full_index)
        # curLine = full_index.readline()
        if not curLine:
            break  # need to break here!
        tempDict = json.loads(curLine)
        for token in tempDict:
            if token in index_of_index:
                print("error, index shouldn't already exist")
            else:
                index_of_index[token] = pos

    if os.path.isfile("index_of_index.txt"):
        os.remove("index_of_index.txt")
    json.dump(index_of_index, open("index_of_index.txt", "w"))


def launch_milestone_1():
    '''our main funciton.'''
    #folder_path = '/home/mnadi/121/A3/search_engine/DEV'
    folder_path = '/home/leviar/121/assign3/search_engine/DEV'
    
    
    #TESTING CHANGE THIS PART TO NORMAL AFTER
    paths = get_file_paths(folder_path)  # list of paths to all the files #ACTUAL
    # paths = ['/home/mnadi/121/A3/search_engine/testing_dev_file.json'] #TESTING
    # TESTING. CHANGE THIS PART TO NORMAL AFTER
    
    count = 0
    global docID
    for path in paths:
        count += 1
        text_content, bold_word_counter = get_file_text_content(path)
        if not text_content:  # skip if no text content
            continue

        # if this file is a duplicate, continue ^^^

        docID += 1
        map_docID_url(path, docID) # assign docID to its proper URL // {docID : url}
        tokens = tokenizer(text_content)  # tokenize the text content
        # token_count = token_counter(tokens)  # count tokens
        token_locs = token_locator(tokens)  # get a list of token positions
        # fill/generate inverted index
    

        generate_inverted_index(token_locs, docID, bold_word_counter)
        if count == 1000: break

    # generate_report()
    
    if os.path.isfile("total_doc_count.txt"):
        os.remove("total_doc_count.txt")
    
    
    total_doc_count = open("total_doc_count.txt", 'w')
    total_doc_count.write(str(docID))
    total_doc_count.close()
    write_remaining_index()
    merge_partial_indexes()  # merges the partial indexes
    create_index_of_index()  # creates index_of_index (global dictionary)
    if os.path.isfile("docID_urls.txt"):
        os.remove("docID_urls.txt")
    json.dump(docID_urls, open("docID_urls.txt", "w"))
    
    print("Done MileStone1!")





if __name__ == '__main__':
    launch_milestone_1()

    # launch_milestone_2()

    # print(index_of_index)
