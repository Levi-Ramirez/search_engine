"""
Plan:
Layout of index file:
    -- 3 sections: 
        - actual index: term entries, one per line in json format
            keep in memory how long each term entry was, write it to index-of-index file
        - index of index: "term, binary_position_in_index_file_in_bytes"
        - textual offset to top level index, padded to 64 chars (read last 64 characters of file, this tells you where to start reading from index of index)

Main idea (indexing):
    1) Read json files and parse them
    2) Create a growing dictionary of terms to their posting information (posting info is also a dictionary, not an object, bc we want be able to write it as json object)
    3) When i reach some num_of_bytes_read limit, dump the current index to disk
        - This is done by using json.dumps() into a text file
        3.1) We stringify the posting information for each term
        3.2) Store json string into the file SORTED by term (per line: term + one term's info)
    4) Once all files have been indexed and we have multiple partial indexes in memory, we merge them
        - This will involve opening all files at the same time, reading in one line at a time, determined alphabetically
        - Make a function to iteratively merge 2 strings of posting info
        - Note that we'll need to create the index of the index (dictionary of term to byte_offset)
        - For posting info of the same term on different files, merge the posting info (dictionary), and update the byte offset accordingly
        - Write the new, finalized posting info for one term into the final index file
    5) Once the final index file is complete, append the index_of_index or create a new file for index_of_index
        - then rewrite the byte offset to the index_of_index as the last 64 bytes of the file

Main idea (querying):
    1) Load the index of index into memory
    2) Split the query string, stem each term, optionally remove stop words
    3) For each term in the query, pull the posting info from the index using the index_of_index
        3.1) hash into index_of_index by term to find term's byte offset into the index
        3.2) seek() the byte offset, extract posting info using readline()
    4) extract docIDs from posting info (one set of DocIDs per query term), find intersection of all sets of docIDs
    5) sort docIDs based on tfidf (using heap)
    6) use docID to hash into dictionary for URLs, display to user
    7) use chatGPT API to get title + summary of document, place title above URL, summary under the url

Things to clarify:
    1) what are we storing per term? list of [term, dictionary key=docid, value=tf]
    2) how does the query work?
        - get posting info for each query term
        - sort the terms by # of keys in dictionary
        - for docid in dictionary sorted by tf, 
            if docid in all other terms, 
                then push tuple of (tfidf sum for cur doc, docID) to heap of common docids (maintain heap length of 5, or 10)
        - 
"""


"""
# how to save to csv
data = [
    {"id": 1, "name": "Object 1", "value": 10},
    {"id": 2, "name": "Object 2", "value": 20},
    {"id": 3, "name": "Object 3", "value": 30}
]

json_data = json.dumps(data)

with open("data.csv", "w", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow([json_data])
"""

"""
# How to use chatGPT API to get summary of text
    1) create account on OpenAI, log in
    2) click "personal" then click "view API keys"
    3) click "create new secret key," and save the key somewhere
    4) install openAI library (pip install openai)
    5) import openai in python script
        openai.my_api_key = 'YOUR_API_KEY'
        messages = [  {"role": "system", "content": "please summarize this text: " + doc_text}  ]
    My key: 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 
        -- i think it's just a hash, i put my name in like so: ColinZejda
        """

import openai
def get_gpt_title_and_summary(doc_text):
    #openai.my_api_key = 'YOUR_API_KEY'     # define it in __init__
    messages_title = [  {"role": "system", "content": "please give a title for this text: " + doc_text}  ]   # may not be necessary
    messages_summary = [  {"role": "system", "content": "please summarize this text: " + doc_text}  ]
    
    title = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages = messages_title)
    summary = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages = messages_summary)

import json
d = [   { "docid" : 15, "pos_list": [1, 34, 50]}, {"docid": 123, "pos_list": [10, 399, 5000]  }  ]  # list of dictionaries (each dictionary has a docid and pos_list as keys)

term_dict = dict()
term_list = list()
file_path = "data.json"
term_offsets = list()     # record of what i've dumped in file (byte offsets)
cur_offset = 0

# open file once, for every term, build term data, write it as json text (string) into a file, remembering byte offset of this data
# everything in one file
    # both the index, as well as the index for the index
with open(file_path, "w") as f:
    for term in term_list:
        #term_data = [(15, [1, 34, 50]), (123, [10, 399, 5000])]        # json data for a term, don't store the term into the index (the term will be kept next to the offset in the index of the index)
        term_data = term_dict[term]
        json_str_term = json.dumps(term_data)                                    # converts json object to string
        f.write(json_str_term)
        term_offsets.append([term, cur_offset])
        cur_offset = f.tell()
    index_of_index_offset = cur_offset     # position of the index of index

    for term, offset in term_list:
        f.write(f"{term} {offset}\n")
    f.write(f"{index_of_index_offset}\n")

def read_index_of_index_offset(file_path):       # use this to read index of index offset
    with open(file_path, "r") as f:
        # Move the file pointer to the end of the file
        f.seek(0, 2)  # 0 offset, relative to the end of the file

        # Find the position of the last newline character
        pos = f.tell()
        while pos > 0:
            pos -= 1
            f.seek(pos)
            if f.read(1) == '\n':
                break

        # Read the last line
        last_line = f.readline()
    return int(last_line)          # aka byte offset to get us to our index_of_index in our file

def read_index_of_index(byte_offset):     # input from read_index_of_index_offset()
    index_of_index = dict()
    with open(file_path, "r") as f:       # file path is our file that contains index, then index_of_index
        f.seek(byte_offset, 0)            # takes us to index_of_index

        for line in f:
            term, offset = line.split()
            index_of_index[term] = offset
    return index_of_index

def read_term_data(byte_offset):          # get a term + its term data
    term_data = None
    with open(file_path, "r") as f:       # file path is our file that contains index, then index_of_index
        f.seek(byte_offset, 0)
        term_data = json.loads(f.readline())          # read one line, which is json string, then loads() it into dict()
    return term_data