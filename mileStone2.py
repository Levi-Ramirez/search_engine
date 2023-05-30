import json
import shelve

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
                baseList.append((posting[0], posting[2]))
        if len(boolean_query_list) == 1: #if its 1 query term, then write out the documents that have that term
            return baseList
        
        for curTerm in boolean_query_list: #for every term in the query list
            for token in curTerm: #should only be 1
                i = 0
                j = 0
                while i < len(baseList): # for every element in the baselist
                    #print("i: ", i)
                    #print("baseList:", baseList)
                    while j < len(curTerm[token]): # for every posting in the current term
                        #print("j:", j)
                        curPosting = curTerm[token][j] #note: curTerm[token][j] gives a posting, curPosting[0] gives the docID
                        if curPosting[0] > baseList[i][0]: 
                            del baseList[i]
                            i -= 1 #decriment it because it will be incrimented later (an incriment + a delition will make it go forward two spots)
                            if len(baseList) == 0:
                                return baseList #return empty list if empty
                            else:
                                break #go to the next element in baselist (with the i+= below), keep current position in curTerm[token]
                        elif curPosting[0] == baseList[i][0]:
                            j += 1 #go to the next element in baselist (with the i+= below), incriment to next position in curTerm[token]
                            break
                        j += 1 #if nothing above, just incriment j to go to the next posting

                    i += 1
    
     
        ranked_posting_list = sorted(baseList, key=lambda x: x[1], reverse=True)
        ranked_posting_docIDs = []
        for post in ranked_posting_list:
            ranked_posting_docIDs.append(post[0])
        return ranked_posting_docIDs

    except Exception as e:
        print('ERROR in generate_boolean_search_result: ', str(e))
        return []
                        

    except Exception as e:
        print('ERROR in generate_boolean_search_result: ', str(e))
        return []

def launch_milestone_2():

    try:
        # index_of_index_shelve = shelve.open("index_of_index.shelve")
        index_of_index = json.load(open("index_of_index_tf_idf.txt"))
        docId_to_urls = json.load(open('docID_urls.txt'))
        # print('docId_to_urls', docId_to_gurls['data'])
        # print('index_of_inverted_index', index_of_inverted_index)
        # print(docId_to_urls)
        query = input("Input your query: \n")
        query_tokens = handle_stopwords(tokenizer(query))
        # ^^ tokenize query and then return a list of tokens after handling the stopwords

        boolean_query_list = []
        # term_being_searched: [post] => [{'decemb': [[4, [1826, 1917], 2]]}, {'deng': [[4, [222], 1]]}, {'depart': [[4, [2687], 1], [9, [108], 1], [12, [84], 1]]}]

        # full_index = open('full_index_tf_idf.txt', 'r')
        full_index = open('full_index_tf_idf.txt', 'r')

        print(query_tokens)
        # print('index_of_index', index_of_index)
        # print('docId_to_urls', docId_to_urls)
        for token in query_tokens:
            if token in index_of_index:
                pos = index_of_index[token]
                # {"11am": [[14, [501], 1]]}
                full_index.seek(pos)
                # line = full_index.readline()
                line = read_large_line(full_index)
                # print('line', line)
                if os.path.isfile('err.txt'):
                    os.remove('err.txt')
                file = open('err.txt', 'w')
                file.write(line)
                file.close()

                posting = json.loads(line)
                boolean_query_list.append(posting)
            else: #if not in index_of_index
                boolean_query_list = [] #set it to an empty list, because this means it found a word that wasn't in any of the documents

        boolean_query_list = sorted(
            boolean_query_list, key=lambda x: len(list(x.values())[0]))
        # [{'decemb': [[4, [1826, 1917], 2]]}, {'deng': [[4, [222], 1]]}, {'depart': [[4, [2687], 1], [9, [108], 1], [12, [84], 1]]}]
        #print(boolean_query_list)
        res = generate_boolean_search_result(boolean_query_list)
        # print('boolean_query_list: ', boolean_query_list)
        if len(res) == 0:
            print('SEARCH RESULT ==> No search results containing all query terms')
        else:
            print('SEARCH RESULT ==> docIDs ', res)
            print('URLS: ')
            for docID in res:
                if str(docID) in docId_to_urls:
                    print(docId_to_urls[str(docID)])
                else:
                    print("THIS SHOULD NOT HAPPEN", docID)

    except Exception as e:
        print('ERROR launch_milestone_2: ', str(e))


launch_milestone_2()