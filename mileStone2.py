import json
import shelve
import time

from sympy import python
from nltk.stem import PorterStemmer  # to stem
from stop_words import get_stop_words
import os
stop_words = set(get_stop_words('en'))


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


def handle_stopwords(query_tokens):
    '''
    if stopwords needed, keeps the original query_tokens and returns query_tokens 
    if stopwords NOT needed, removes the stopwords and  returns query_tokens_no_stop_words
    '''
    global stop_words

    query_tokens_no_stop_words = []
    removed = []
    for token in query_tokens:
        if token in stop_words:
            removed.append(token)
            continue
        else:
            query_tokens_no_stop_words.append(token)

    loss_percentange = 100 - ((len(query_tokens_no_stop_words)
                               * 100) / len(query_tokens))

    if loss_percentange >= 50:  # more than 50 percent of the query is lost. stop words needed
        return query_tokens
    return query_tokens_no_stop_words  # stop words NOT needed, remove them


def read_large_line(file):
    chunk_size = 4096  # python line buffer size
    line = ''

    while True:
        chunk = file.readline(chunk_size)
        line += chunk

        if len(chunk) < chunk_size or '\n' in chunk:
            break

    return line


#OLD BUT TESTED generate_boolean_search
# def generate_boolean_search_result(boolean_query_list):

#     try:
#         search_result_docIDs = []
#         # {'decemb': [[4, [1826, 1917], 2]]} => {word: [[docID, [positions...], frequency]]}
#         if len(boolean_query_list) == 0:
#             return search_result_docIDs #return the empty set
#         least_seen_word_object = boolean_query_list[0]
#         # print("least seen word: ", least_seen_word_object)
#         least_seen_word = list(boolean_query_list[0].keys())[0]  # decemb
#         # print("least_seen_word_object[least_seen_word]", least_seen_word_object[least_seen_word])
#         # print(len(boolean_query_list))
#         baseList = [] #baseList is the list of docID's that are in the least_seen_word
#         for posting in least_seen_word_object[least_seen_word]:
#                 baseList.append(posting[0])
#         if len(boolean_query_list) == 1: #if its 1 query term, then write out the documents that have that term
#             return baseList

#         #filter base list

#         # minTFIDF = 
#         #first100Count = 100
        
#         print("this far")
#         for curTerm in boolean_query_list: #for every term in the query list
#             for token in curTerm: #should only be 1
#                 i = 0
#                 j = 0
#                 while i < len(baseList): # for every element in the baselist
#                     #print("i: ", i)
#                     #print("baseList:", baseList)
#                     while j < len(curTerm[token]): # for every posting in the current term
#                         #print("j:", j)
#                         curPosting = curTerm[token][j] #note: curTerm[token][j] gives a posting, curPosting[0] gives the docID
#                         if curPosting[0] > baseList[i]: #if current posting's doc id is greater than the baseList's doc id
#                             del baseList[i]
#                             i -= 1 #decriment it because it will be incrimented later (an incriment + a delition will make it go forward two spots)
#                             if len(baseList) == 0:
#                                 return baseList #return empty list if empty
#                             else:
#                                 break #go to the next element in baselist (with the i+= below), keep current position in curTerm[token]
#                         elif curPosting[0] == baseList[i]:
#                             j += 1 #go to the next element in baselist (with the i+= below), incriment to next position in curTerm[token]
#                             break
#                         j += 1 #if nothing above, just incriment j to go to the next posting

#                     i += 1
    
#         return baseList
                        

#     except Exception as e:
#         print('ERROR in generate_boolean_search_result: ', str(e))
#         return []



#MOST RECENT MODIFICATIONS BELOW
def generate_boolean_search_result(boolean_query_list):
 
    try:
        search_result_docIDs = []
        # {'decemb': [[4, [1826, 1917], 2]]} => {word: [[docID, [positions...], frequency]]}
        if len(boolean_query_list) == 0:
            return search_result_docIDs #return the empty set
        least_seen_word_object = boolean_query_list[0]
        # print("least seen word: ", least_seen_word_object)
        least_seen_word = list(boolean_query_list[0].keys())[0]  # decemb
        # print("least_seen_word_object[least_seen_word]", least_seen_word_object[least_seen_word])
        # print(len(boolean_query_list))
        baseList = [] #baseList is the list of docID's that are in the least_seen_word
        
        for posting in least_seen_word_object[least_seen_word]:
                baseList.append([posting[0], posting[2]])
                # docIDList.append(posting[0])
        if len(boolean_query_list) == 1: #if its 1 query term, then write out the documents that have that term
            return baseList

        #filter base list

        minTFIDF = 0
        firstFewCount = 150
        
        #print("this far")
        for curTerm in boolean_query_list: #for every term in the query list
            for token in curTerm: #should only be 1
                i = 0
                j = 0
                while i < len(baseList): # for every element in the baselist
                    #print("i: ", i)
                    #print("baseList:", baseList)

                    #calculate new minimum tf-idf to look for up until the "firstFewCount" runs out
                    if firstFewCount > 0:
                        firstFewCount -= 1
                        if minTFIDF > baseList[i][1]: #compare current minimum with the base list
                            minTFIDF = baseList[i][1]
                    else:
                        if minTFIDF > baseList[i][1]:
                            print("deletes...")
                            del baseList[i]
                            continue

                    while j < len(curTerm[token]): # for every posting in the current term
                        #print("j:", j)
                        curPosting = curTerm[token][j] #note: curTerm[token][j] gives a posting, curPosting[0] gives the docID
                        if curPosting[0] > baseList[i][0]: #if current posting's doc id is greater than the baseList's doc id
                            del baseList[i]
                            i -= 1 #decriment it because it will be incrimented later (an incriment + a delition will make it go forward two spots)
                            if len(baseList) == 0:
                                return baseList #return empty list if empty
                            else:
                                break #go to the next element in baselist (with the i+= below), keep current position in curTerm[token]
                        elif curPosting[0] == baseList[i][0]: #if current posting has the same docID, add it to the list and add to baseList docID's tf-idf
                            baseList[i][1] += curPosting[2]
                            j += 1 #go to the next element in baselist (with the i+= below), incriment to next position in curTerm[token]
                            break
                        j += 1 #if nothing above, just incriment j to go to the next posting

                    i += 1
        # print("HEREEEE")
        # print("baseList: ", baseList)
        # docIDList = []
        # for x in baseList:
        #     docIDList.append(x[0])
        # print("docIDList: ", docIDList)
        # print("baseList: ", baseList)

        baseList.sort(key = lambda x: x[1], reverse = True) #sort according to tfIDF
        if len(baseList) > 500: #get the top 200 documents
            baseList = baseList[:500]
        return baseList

        # return docIDList
                        

    except Exception as e:
        print('ERROR in generate_boolean_search_result: ', str(e))
        return []



# def generate_boolean_search_result(boolean_query_list):

#     try:
#         search_result_docIDs = []
#         # {'decemb': [[4, [1826, 1917], 2]]} => {word: [[docID, [positions...], frequency]]}
#         if len(boolean_query_list) == 0:
#             return search_result_docIDs #return the empty set
#         least_seen_word_object = boolean_query_list[0]
#         # print("least seen word: ", least_seen_word_object)
#         least_seen_word = list(boolean_query_list[0].keys())[0]  # decemb
#         # print("least_seen_word_object[least_seen_word]", least_seen_word_object[least_seen_word])
#         # print(len(boolean_query_list))
#         baseList = [] #baseList is the list of docID's and tf-idfID's that are in the least_seen_word
#         for posting in least_seen_word_object[least_seen_word]:
#                 baseList.append([posting[0], posting[2]])
#         if len(boolean_query_list) == 1: #if its 1 query term, then write out the documents that have that term
#             return baseList

#         #filter base list

#         minTFIDF = 0
#         first200Count = 200 # threshold

        
#         print("this far")
#         for curTerm in boolean_query_list: #for every term in the query list
#             for token in curTerm: #should only be 1
#                 i = 0
#                 j = 0
#                 while i < len(baseList): # for every element in the baselist

#                     # #calculate new minimum tf-idf to look for
#                     # if first200Count > 0:
#                     #     first200Count -= 1
#                     #     if minTFIDF > baseList[i][1]: #compare current minimum with the base list
#                     #         minTFIDF = baseList[i][1]
#                     # else:
#                     #     if minTFIDF > baseList[i][1]:
#                     #         del baseList[i]
#                     #         continue

#                     #print("i: ", i)
#                     #print("baseList:", baseList)
#                     while j < len(curTerm[token]): # for every posting in the current term
#                         #print("j:", j)
#                         curPosting = curTerm[token][j] #note: curTerm[token][j] gives a posting, curPosting[0] gives the docID
#                         if curPosting[0] > baseList[i][0]: #if current posting's doc id is greater than the baseList's doc id
#                             del baseList[i]
#                             i -= 1 #decriment it because it will be incrimented later (an incriment + a delition will make it go forward two spots)
#                             if len(baseList) == 0:
#                                 return baseList #return empty list if empty
#                             else:
#                                 break #go to the next element in baselist (with the i+= below), keep current position in curTerm[token]
#                         elif curPosting[0] == baseList[i][0]:
#                             j += 1 #go to the next element in baselist (with the i+= below), incriment to next position in curTerm[token]
#                             break
#                         j += 1 #if nothing above, just incriment j to go to the next posting

#                     i += 1
    
#         return baseList
                        

    except Exception as e:
        print('ERROR in generate_boolean_search_result: ', str(e))
        return []

def docOrder(query_docsID_tfidf, boolean_query_list): #query term list, query document result
    '''returns a list of lists [[docID-1, tfidf-1], [docID-2, tfidf-2]] in order of decreasing tfidf'''
    doc_ngram_count = []
    intesection_docID = set()
    for docID_tfidf in query_docsID_tfidf:
        docID = docID_tfidf[0]
        tfidf = docID_tfidf[1]
        partial_ngrams = nGramDoc(docID, boolean_query_list) #returns an int of the number of partial ngrams found
        doc_ngram_count.append([docID, partial_ngrams + tfidf])
        intesection_docID.add(docID)
    
    doc_ngram_count = sorted(doc_ngram_count, key = lambda x: x[1], reverse = True)
    return (doc_ngram_count, intesection_docID)


#returns an int of the number of partial ngrams found
def nGramDoc(docID, boolean_query_list):
    #print("nGramDoc:")
    tokenPosInDoc = [] #token positions will be a list of lists (one list of positions for each document)
    tfidfScore = 0
    for posting_list in boolean_query_list:
        found = False
        for token in posting_list: #should only be 1
            for posting in posting_list[token]:
                if posting[0] == docID: #when you find the docID for this posting, return its list of positions
                    found = True
                    tokenPosInDoc.append(posting[1]) #get its positions in this document
                    tfidfScore = posting[2] #get its current tfidf
                    break
            if found:
                break
    #print("tokenPosInDoc: ", tokenPosInDoc)
    indexPos = [0] * len(tokenPosInDoc) #indexPos is the current index you are looking at for that token in this document
    count = 0 #count is the number of times you found sequential words in the order of which they were entered
    lastIndex = len(indexPos) - 1 #save the last index

    minIndex = getMinIndex(indexPos, tokenPosInDoc)
    while(True):
        # if lastIndex == minIndex:
        #     indexPos[minIndex] += 1 #incriment the next minimum index of this term
        #     minIndex = getMinIndex(indexPos, tokenPosInDoc)
        if lastIndex != minIndex and tokenPosInDoc[minIndex][indexPos[minIndex]] - tokenPosInDoc[minIndex + 1][indexPos[minIndex + 1]] == 1:
            count += 1
            indexPos[minIndex] += 1 #incriment the next minimum index of this term
            if(len(tokenPosInDoc[minIndex]) <= indexPos[minIndex]): #if it reached the end of this list, break cuz the query n-gram is not not relavent
                break
                
            minIndex += 1 #make the minIndex one more as the next term is shown to follow this one
        else: #if the index after it is not the next word in the query and it is not the last index, then incriment the current term and compute the next index
            indexPos[minIndex] += 1 #incriment the next minimum index of this term
            if(len(tokenPosInDoc[minIndex]) <= indexPos[minIndex]): #if it reached the end of this list, break cuz the query n-gram is not not relavent
                break
            minIndex = getMinIndex(indexPos, tokenPosInDoc)
    #return count, tfidfScore
    return count

        

        

def getMinIndex(indexPos, tokenPosInDoc):
    i = 0
    minIndex = 0
    curMinVal = 0
    while i < len(indexPos):
        if tokenPosInDoc[i][indexPos[i]] < curMinVal:
            curMinVal = tokenPosInDoc[i][indexPos[i]] 
            minIndex = i
        i += 1
    
    return minIndex




# def generate_boolean_or_search_result(boolean_query_list, intersection_docIDs):
    
#     try:
#         posting_union = []
#         limit = 0
        
#         for index_obj in boolean_query_list: #index_obj = {'shindler': [[1948, [1065], 11.18], [3962, [133], 11.18], [6197, [37], 33.53], [7084, [82], 11.18], [7355, [92], 11.18], [8487, [20], 33.53], [9391, [32], 11.18], [11356, [31], 33.53], [17341, [58], 11.18]]}
#             if limit >= 50:
#                 break
#             token = list(index_obj.keys())[0] # token = 'shindler'
            
#             for posting in index_obj[token]:
#                 docID = posting[0]
#                 if docID not in intersection_docIDs:
#                     posting_union.append(posting)
#                     intersection_docIDs.add(docID)

#         postings_union_ranked = sorted(posting_union, key=lambda x: x[2], reverse=True)
        
#         ranked_posting_docIDs = []
        
#         for posting in postings_union_ranked:
#             ranked_posting_docIDs.append(posting[0]) #pushing docID 
            
#         return ranked_posting_docIDs

#     except Exception as e:
#         print('ERROR in generate_boolean_or_search_result: ', str(e))
#         return []
def generate_boolean_or_search_result(boolean_query_list, intersection_docIDs):
    
    try:
        posting_union = []
        limit = 0
        
        for index_obj in boolean_query_list: #index_obj = {'shindler': [[1948, [1065], 11.18], [3962, [133], 11.18], [6197, [37], 33.53], [7084, [82], 11.18], [7355, [92], 11.18], [8487, [20], 33.53], [9391, [32], 11.18], [11356, [31], 33.53], [17341, [58], 11.18]]}
            if limit >= 50:
                break
            token = list(index_obj.keys())[0] # token = 'shindler'
            
            for posting in index_obj[token]:
                docID = posting[0]
                if docID not in intersection_docIDs:
                    posting_union.append([posting[0], posting[2]])
                    intersection_docIDs.add(docID)

        postings_union_ranked = sorted(posting_union, key=lambda x: x[1], reverse=True)
        
        
        return postings_union_ranked[0:50]

    except Exception as e:
        print('ERROR in generate_boolean_or_search_result: ', str(e))
        return []



def launch_milestone_2(index_of_index, docId_to_urls, query):

    try:

        # index_of_index_shelve = shelve.open("index_of_index.shelve")
        # index_of_index = json.load(open("index_of_index.txt"))
        # index_of_index = json.load(open("index_of_index_tf_idf.txt"))
        # docId_to_urls = json.load(open('docID_urls.txt'))
        # # print('docId_to_urls', docId_to_gurls['data'])
        # # print('index_of_inverted_index', index_of_inverted_index)
        # # print(docId_to_urls)
        # query = input("Input your query: \n")
        query_tokens = handle_stopwords(tokenizer(query))
        # ^^ tokenize query and then return a list of tokens after handling the stopwords

        boolean_query_list = []
        # term_being_searched: [post] => [{'decemb': [[4, [1826, 1917], 2]]}, {'deng': [[4, [222], 1]]}, {'depart': [[4, [2687], 1], [9, [108], 1], [12, [84], 1]]}]

        # full_index = open('full_index.txt', 'r')
        full_index = open('full_index_tf_idf.txt', 'r')

        #print(query_tokens)
        # print('index_of_index', index_of_index)
        # print('docId_to_urls', docId_to_urls)
        startTime = time.time()
        for token in query_tokens:
            #print('token', token)
            if token in index_of_index:
                pos = index_of_index[token]
                #print('pos', pos)
                # {"11am": [[14, [501], 1]]}
                full_index.seek(pos)
                # line = full_index.readline()
                line = read_large_line(full_index)
                # print('line', line)
                #print('making file')
                if os.path.isfile('err.txt'):
                    os.remove('err.txt')
                file = open('err.txt', 'w')
                file.write(line)
                file.close()

                posting = json.loads(line)
                boolean_query_list.append(posting)
            else: #if not in index_of_index
                boolean_query_list = [] #set it to an empty list, because this means it found a word that wasn't in any of the documents
            
        totalTime = (time.time() - startTime) * 100
        print("get boolean_query_list: ", totalTime)

        boolean_query_list_sorted = sorted(
            boolean_query_list, key=lambda x: len(list(x.values())[0]))
        # [{'decemb': [[4, [1826, 1917], 2]]}, {'deng': [[4, [222], 1]]}, {'depart': [[4, [2687], 1], [9, [108], 1], [12, [84], 1]]}]
        #print(boolean_query_list)
        #print("bool_query_list len: ", len(boolean_query_list))
        #print("bool_query_list: ", boolean_query_list)
        startTime = time.time()
        query_docsID_tfidf = generate_boolean_search_result(boolean_query_list_sorted) #res is the docID's which gets all of the docs that contain the terms in the boolean_query_list
        totalTime = (time.time() - startTime) * 100
        print("generate_boolean_search_result: ", totalTime)
        #nGram the list and return them and their weights by assorted order



        # STARTING NOW:
        startTime = time.time()
        final_list_docIDs_tfidf, intesection_docID = docOrder(query_docsID_tfidf, boolean_query_list) #query term list, query document result

        #if there are not enough docs, add more based on max tfidf for each boolean_qeury_list item
        or_res = generate_boolean_or_search_result(boolean_query_list_sorted, intesection_docID) if len(final_list_docIDs_tfidf) < 50 else []#final_l
        print("or_res: ", or_res)

        #append the list of lists
        final_list_docIDs_tfidf = final_list_docIDs_tfidf + or_res
        totalTime = (time.time() - startTime) * 100
        print("docOrder: ", totalTime)

        startTime = time.time()
        #docFile = open('docID_urls.txt', 'r')
        docDict = json.load(open("docID_urls.txt"))
        #print("doctDict: ", docDict)
        final_list_urls_tfidf = []
        for docID_tfidf in final_list_docIDs_tfidf:
            #print("docID_tfidf: ", docID_tfidf)
            docID = str(docID_tfidf[0])
            tfidf = docID_tfidf[1]
            url = docDict[docID]
            final_list_urls_tfidf.append([url, tfidf])
        
        totalTime = (time.time() - startTime) * 100
        print("get [url, tfidf]: ", totalTime)
        
        #print(final_list_urls_tfidf) #
            

        #docFile.close()

        if len(query_docsID_tfidf) == 0:
            print('SEARCH RESULT ==> No search results containing all query terms')
        # else:
            #print("nothing")
            # print('SEARCH RESULT ==> docIDs ', query_docs)
            # print('URLS: ')
            # for docID in res:
            #     if str(docID) in docId_to_urls:
            #         print(docId_to_urls[str(docID)])
            #     else:
            #         print("THIS SHOULD NOT HAPPEN", docID)
        print(final_list_urls_tfidf)

    except Exception as e:
        print('ERROR launch_milestone_2: ', str(e))

index_of_index = json.load(open("index_of_index_tf_idf.txt"))
docId_to_urls = json.load(open('docID_urls.txt'))
# print('docId_to_urls', docId_to_gurls['data'])
# print('index_of_inverted_index', index_of_inverted_index)
# print(docId_to_urls)
query = input("Input your query: \n")
startTime = time.time()
launch_milestone_2(index_of_index, docId_to_urls, query)
endTime = time.time()
totalTimeMS = (endTime - startTime) * 100
print("Time it took in mili-seconds: ", totalTimeMS)