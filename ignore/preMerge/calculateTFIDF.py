

import json
import os

import math


def calculate_tf_idf(index_obj, key, total_doc_count):
    '''
    formula = (1 + log(tf)) * log(N / df)
    tf = len(posting[1]) AKA term_frequency 
    N = total_doc_count
    df = len(index_obj[key]) AKA document_frequency

    '''
    try:
        N = total_doc_count
        df = len(index_obj[key])
        for posting in index_obj[key]: # posting = [28695, [30088, 70088], 2] IN = [[28695, [30088, 70088], 2], [31095, [152875], 1], [32761, [30088, 70088], 2], [40645, [14678], 1], [41010, [355455], 1], [55365, [5436462, 6634496, 9478486], 3]]
            #posting[0] = docID
            #posting[1] = positions "key" found in docID 
            #len(posting[1]) = term_frequency
            # posting[2] = where we will put td-idf
            tf = len(posting[2])

            tf_idf = (1 + math.log(tf, 2)) * math.log((N / df), 2)
            # print('before: ', posting[2])
            posting[2] = tf_idf
            # print('after: ', posting[2])
            
        
        return index_obj
    except Exception as e:
        print("ERROR in calculate_tf_idf: ", str(e))
        
        
def generate_full_index_tf_idf():
    '''generates a txt file of a full_index with actaul tf-idf scores'''
    
    
    try:
        full_index = open('full_index.txt', 'r')
        total_doc_count = int(open('total_doc_count.txt', 'r').readline())




        if os.path.isfile("full_index_tf_idf.txt"):
            os.remove("full_index_tf_idf.txt")
        full_index_tf_idf = open('full_index_tf_idf.txt', 'w')

        # testing_break = 0 #remove this
        
        while True:
            # if testing_break >= 1: #remove this
                # break

            index_txt= read_large_line(full_index)
            if not index_txt: #if line is empty, end is reached, break
                break
            index_obj = json.loads(index_txt) #{"000000000000003518": [[33278, [2697], 1]]}
            key = list(index_obj.keys()) 
            key = key[0] #key = '000000000000003518'
            index_obj_tf_idf = calculate_tf_idf(index_obj, key, total_doc_count)

            json.dump(index_obj_tf_idf, full_index_tf_idf)
            full_index_tf_idf.write('\n')
            # testing_break += 1 #remove this 
        full_index_tf_idf.close()
        full_index.close()
    except Exception as e:
        print("ERROR in generate_full_index_tf_idf: ", str(e))

def read_large_line(file):
    chunk_size = 4096  # python line buffer size
    line = ''

    while True:
        chunk = file.readline(chunk_size)
        line += chunk

        if len(chunk) < chunk_size or '\n' in chunk:
            break

    return line





if __name__ == '__main__':
    print('running...')
    generate_full_index_tf_idf()
    print('done')