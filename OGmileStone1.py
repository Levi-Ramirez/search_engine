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
import nltk
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

#instead, lets try to define a list


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

def write_to_file(thisFile, newDict):
    # for key, val in newDict.items():
    #     tempDict = {key: val}
    #     json.dump(tempDict, thisFile)
    #     thisFile.write('\n')
    for key in newDict:
        tempDict = {key: newDict[key]}
        json.dump(tempDict, thisFile)
        thisFile.write('\n')



def generate_inverted_index(token_locs, docID):
    '''this function generates/fills the inverted_index. Gets count_tokes and docID as parameters.'''
    global indexSplitCounter
    global fileCount
    indexSplitCounter += 1
    if indexSplitCounter > 5:
        fileName = "index" + str(fileCount) + ".txt"
        if os.path.exists(fileName):
            os.remove(fileName)
        with open(fileName, "w") as thisFile:
            res = sorted(inverted_index.items())
            newDict = dict(res)
            # json.dump(newDict, thisFile)  REPLACE THIS LINE
            write_to_file(thisFile, newDict) #replacement
        
        inverted_index.clear()
        indexSplitCounter = 0
        fileCount += 1
    try:
        for token in token_locs:
            # tfidf = round(count_tokens[token] / len(count_tokens), 4)
            tfidf = len(token_locs[token])
            # post = Posting(docID, token_locs[token], tfidf)
            post = [docID, token_locs[token], tfidf]
            if token in inverted_index:
                inverted_index[token].append(post)
            else:
                inverted_index[token] = [post]
    except Exception as e:
        print(f"Error Generating Inverted Index {docID} : {str(e)}")

def getKey(myStr):
    firstQuote = myStr.find('"')
    secondQuote = myStr.find('"', firstQuote + 1)
    if firstQuote == -1 or secondQuote == -1: #if there is no key, return empty string
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
            for posting in dictHolder[key]: #for every posting already in the dictHolder
                if (posting[0] > dict2List[k][0]):
                    # dictHolder[key].insert(i, dictHolder[key].insert(dict2List[k]))
                    dictHolder[key].insert(i, dict2List[k])
                    k =+ 1
                    if k >= len(dict2List): #reached the end
                        break
                i += 1
            
            while k < len(dict2List): # if we havent reached the end of dict2List
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
    while tempCount < fileCount: #open all files loop
        fileName = "index" + str(tempCount) + ".txt"
        tempHolder = open(fileName, "r")
        arrFiles.append(tempHolder)
        tempCount += 1
    arrNextMinIndexesText = []
    arrNextMinIndexesDict = []
    # while True:
    tempCount = 0
    while tempCount < fileCount:
        arrNextMinIndexesText.append(arrFiles[tempCount].readline()) #will be a list of dictionary entries represented by text
        arrNextMinIndexesDict.append(json.loads(arrNextMinIndexesText[tempCount])) #will be a list of ACTUAL dictionary entries
        tempCount += 1
    # minKey = getKey(arrNextMinIndexesText[0])
    while(True):
        minKey = ""
        for x in arrNextMinIndexesText: #gets the first non-empty string and assign it to minKey
            if x != "":
                minKey = x
                break
        if minKey == "": #means that all of them were empty strings, nothing else to read from all files
            break

        for x in arrNextMinIndexesText:
            curKey = getKey(x)
            if curKey != "" and (curKey < minKey):
                minKey = curKey
        # if(minKey == float('inf')): 
        #     break
        i = 0
        dictHolder = {} #holder is the new dictionary which we will write to the file
        # print(arrNextMinIndexesDict)
        #print(minKey)
        
        while i < fileCount:
            if minKey in arrNextMinIndexesDict[i]:
                # print(arrNextMinIndexesDict[i])
                merge_step(dictHolder, arrNextMinIndexesDict[i])
                # print(dictHolder)
                arrNextMinIndexesText[i] = arrFiles[i].readline() #update this to the next line
                if(arrNextMinIndexesText[i] != ""):
                    arrNextMinIndexesDict[i] = json.loads(arrNextMinIndexesText[i]) # update this to the next dict entry
            i += 1
        #print(dictHolder)
        json.dump(dictHolder, full_index)
        full_index.write('\n')
        


    tempCount = 0
    while tempCount < fileCount: #close all files loop
        arrFiles[tempCount].close()
        tempCount += 1
    full_index.close()

'''OLD CODE'''
# def merge_partial_indexes():
#     global fileCount
#     tempCount = 0
#     arr = []
#     while tempCount < fileCount: #open all files loop
#         fileName = "index" + str(tempCount) + ".txt"
#         tempHolder = open(fileName, "r")
#         arr.append(tempHolder)
#         #read and throw away the first {
#         arr[tempCount].read(1)
#         tempCount += 1
    
    
#     #read in 50 indexes for each file (or until the end of the file):
#     buffArr = []
#     buffArrLeftOver = []
#     tempCount = 0
#     buffArr.append(arr[0].read(10)) #read 500 characters and store in buffArr
#     buffArrLeftOver.append(buffArr[0][leftOverBegin + 2:])
#     buffArr.append(arr[1].read(10)) #read 500 characters and store in buffArr
#     buffArrLeftOver.append(buffArr[1][leftOverBegin + 2:])
#     buffArr.append(arr[2].read(10)) #read 500 characters and store in buffArr MODIFY THESE
#     buffArrLeftOver.append(buffArr[2][leftOverBegin + 2:])
#     while tempCount < fileCount:
        
#         # ADD LEFTOVER HERE
#         bufArr[tempCount] = buffArrLeftOver[tempCount] +  buffArr[tempCount] #append old leftover to the continued read
#         leftOverBegin = buffArr[tempCount].rindex(']]')
#         # buffArrLeftOver = buffArr[tempCount][leftOverBegin + 2:]
#         bufArr[tempCount] = buffArr[tempCount][:leftOverBegin + 2]#get rid of the leftover

#                 #     print(character)
#                 # else:
#                 #     continue  # Continue to the next line if the desired string is not found in the current line
#                 # break  # Break the outer loop if the desired string is found in a line
#         tempCount += 1
            

#     tempCount = 0
#     while tempCount < fileCount: #close all files loop
#         arr[tempCount].close()
#         tempCount += 1
    
    



# def token_counter(tokens):
#     '''this funciton returns a dictionary of words as keys and number of occurences of those words as values'''
#     token_count = {}
#     for token in tokens:
#         if not token:
#             continue
#         if token in token_count:
#             token_count[token] += 1
#         else:
#             token_count[token] = 1

#     return token_count

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
    '''This function generates our report for milestone 1. It will print the word and the list of all the documents that word seen and frequency of that word in that doc. for example, "random_word": [(1, 0.24) (99, 0.0029) ... ] where every tupple is (docID, frequency)'''
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

        file_path = 'path_to_your_file'  # Replace with the actual file path

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
        curLine = full_index.readline()
        if not curLine:
            break #need to break here!
        tempDict = json.loads(curLine)
        for token in tempDict:
            if token in index_of_index:
                print("error, index shouldn't already exist")
            else:
                index_of_index[token] = pos
        


def launch_milestone_1():
    '''our main funciton.'''
    # folder_path = '/home/mnadi/121/A3/search_engine/DEV'
    folder_path = '/home/leviar/121/assign3/search_engine/DEV'
    paths = get_file_paths(folder_path)  # list of paths to all the files
    for path in paths:
        global docID
        if docID >= 20:
             break

        # text_content of file located at path
        text_content = get_file_text_content(path)
        if not text_content:  # skip if no text content
            continue

        # if this file is a duplicate, continue ^^^

        docID += 1
        # assign docID to its proper URL // {docID : url}
        map_docID_url(path, docID)
        tokens = tokenizer(text_content)  # tokenize the text content
        # token_count = token_counter(tokens)  # count tokens
        token_locs = token_locator(tokens)  # get a list of token positions
        # fill/generate inverted index
        generate_inverted_index(token_locs, docID)
    
    generate_report()
    merge_partial_indexes() #merges the partial indexes
    create_index_of_index() #creates index_of_index (global dictionary)


def launch_milestone_2():
    userInput = input("Enter query:")
    print(userInput)
    listTokensInfo = []
    termList = tokenizer(userInput)
    print(termList)
    #AND only query process:

    # retrieve the queries
    full_index = open("full_index.txt", 'r')
    
    for x in termList:
        if x in index_of_index:
            #retrieve the term information, place it in a list of lists
            pos = index_of_index[x]
            full_index.seek(pos)
            curLine = full_index.readline()
            tempDict = json.loads(curLine)
            for token in tempDict:
                listTokensInfo.append(tempDict[token])
    print(listTokensInfo)
    # find their intersection
    

if __name__ == '__main__':
    launch_milestone_1()
    print(index_of_index)
    #launch_milestone_2()

    # print(index_of_index)



