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
        intersection_docIDs = set()
        intersection_postings = []
        # {'decemb': [[4, [1826, 1917], 2]]} => {word: [[docID, [positions...], frequency]]}
        least_seen_word_object = boolean_query_list[0]
        least_seen_word = list(boolean_query_list[0].keys())[0]  # decemb

        # looping outher list of 2d array: [[4, [1826, 1917], 2]]
        for post in least_seen_word_object[least_seen_word]:
            cur_doc_id = post[0]  # [4, [1826, 1917], 2] => cur_doc_id = 4
            if len(boolean_query_list) == 1:
                return [cur_doc_id]
            # starting from index 1 becasue least_seen_word is at index 0
            for i in range(1, len(boolean_query_list)):
                # {'day': [[1, [150], 1], [2, [150], 1], [3, [150], 1]]}
                cur_word_object = boolean_query_list[i]
                cur_word = list(boolean_query_list[i].keys())[0]  # day

                # [[1, [150], 1], [2, [150], 1], [3, [150], 1]]
                for nxt_post in cur_word_object[cur_word]:
                    nxt_doc_id = nxt_post[0]
                    if nxt_doc_id == cur_doc_id:
                        if nxt_doc_id in intersection_docIDs:
                            continue
                        intersection_docIDs.add(nxt_doc_id)
                        intersection_postings.append(nxt_post)
                        break
                    elif nxt_doc_id > cur_doc_id:
                        return []  # bc no solution with boolean AND
                    # else continue. there might be a soluiton
        
        ranked_posting_list = sorted(intersection_postings, key=lambda x: x[2], reverse=True)
        print('ranked_posting_list', ranked_posting_list)
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