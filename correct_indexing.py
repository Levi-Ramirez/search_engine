"""
Plan:
Layout of index file:
    -- 3 sections: 
        - actual index: term entries, one per line in json format
            keep in memory how long each term entry was, write it to index-of-index file
        - index of index: "hot binary_position_in_file_in_bytes"
        - textual offset to top level index, padded to 64 chars 
            (read last 64 characters of file, this tells you where to start reading from index of index)

Steps to build one big index file:
    1) create dictionary: key = term, value = dictionary of dictionaries
"""
import json
d = [   { "docid" : 15, "pos_list": [1, 34, 50]}, {"docid": 123, "pos_list": [10, 399, 5000]  }  ]  # list of dictionaries (each dictionary has a docid and pos_list as keys)

term_list = []
file_path = "data.json"
term_offsets = list()     # record of what i've dumped in file (byte offsets)
cur_offset = 0

# open file once, for every term, build term data, write it as json text (string) into a file, remembering byte offset of this data
# everything in one file
    # both the index, as well as the index for the index
with open(file_path, "w") as f:
    for term in term_list:
        term_data = [(15, [1, 34, 50]), (123, [10, 399, 5000])]        # json data for a term
        json.dumps(term_data, f)                                    # converts json object to string
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