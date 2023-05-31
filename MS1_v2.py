from bs4 import BeautifulSoup
import shelve
import json
from nltk.stem import PorterStemmer        # stemming
from nltk.tokenize import word_tokenize    # tokenizer
import psutil                       # for RAM usage check 
import math                         # for log when calculating tfidf
import os                           # for files (get size, file paths)
import sys                          # get size of a data structure
import time
import re
import heapq
    
class InvertedIndex:
  def __init__(self):
    self.docID_to_url = dict()       # dict, key: docID, val: url string, len(self.docID_to_url) = # of documents in corpus
    self.ps = PorterStemmer()
    self.num_partial_indexes = 0     # for naming partial indexes
    self.num_documents = 0

  def get_json_file_paths(self, root_dir):
    json_paths = []
    for cur_dir, all_dirs, all_files in os.walk(root_dir):     # os.walk() traverses a directory tree using DFS, iterating over all files and directories in it
      for f in all_files:
        if f.endswith(".json"):
          json_paths.append(os.path.join(cur_dir, f))
    self.num_documents = len(json_paths)
    return json_paths #[:1000]

  def is_json_file_size_within_ram_limit(self, file_path):         # can comment out to increase indexing speed
    file_size_in_bytes = os.path.getsize(file_path)
    ram_size_in_bytes = psutil.virtual_memory().total
    ram_limit_in_bytes = 0.75 * ram_size_in_bytes

    return file_size_in_bytes <= ram_limit_in_bytes

  def tokenizer(self, json_file_path):
    try:
      if self.is_json_file_size_within_ram_limit(json_file_path):
        # load the json file, each json file has: URL, Content, Encoding (ascii or utf-8)
        with open(json_file_path, 'r') as f:
          json_data = json.load(f)     # read contents of file and converts it into a python dict or lists
      
        # use BS4 to get text content
        html_content = json_data["content"]
        url = json_data["url"]
        soup = BeautifulSoup(html_content, 'html.parser')
        soup.prettify()  # fix broken HTML
        page_text_content = soup.get_text()

        # get important fields (headings h, bolded b, and strong)
        # add more occurrences of them to boost
        important_h_b_strong = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'strong'])
        for tag in important_h_b_strong:
          if '<h1' in tag:
            page_text_content += (tag.text * 100)          # remember, this increases tf, which we take log_10 of later
          elif '<h2' in tag:
            page_text_content += (tag.text * 50)
          elif '<h3' in tag or 'b' in tag or 'strong' in tag:
            page_text_content += (tag.text * 25)
          elif '<h4' in tag:
            page_text_content += (tag.text * 10)
          elif '<h5' in tag:
            page_text_content += (tag.text * 5)
          elif '<h6' in tag:
            page_text_content += (tag.text * 3)

        # get tokens from text content, lower() + stem() them
        tokens = word_tokenize(page_text_content)
        stemmed_tokens = [self.ps.stem(token.lower()) for token in tokens if token.isalnum()]
        return stemmed_tokens, url 
      else:
        print("File size exceeded RAM.\n")
        return [], ""
    
    except:
      print(f"Encountered exception, file: {json_file_path}")
      return [], ""


  def create_postings(self, docID, tokens):
    # Note: THIS IS FOR ONE DOCUMENT (but all terms within)
    dict_term_to_posting = dict()
    for t in tokens:          # go thru list of tokens
      if t not in dict_term_to_posting:
        dict_term_to_posting[t] = [docID, 0]           # list of 2
      dict_term_to_posting[t][1] += 1

    return dict_term_to_posting          # this is a dictionary, key=term, val=list of [docID, tf]


  def create_and_store_partial_indexes(self, root_dir):
    json_file_paths = self.get_json_file_paths(root_dir)
    with open("file_paths.txt", "w") as fps:               # index of each file path = docID
      json.dump(json_file_paths, fps)
    current_partial_index_dict = dict()                        # partial index that will be stored to disk, key = term, val = list of lists, first element isn't a list, it's the term string, followed by inner lists: [docID_list, tf]

    # to check speed of indexing
    # start_time = time.time()
    # last_ts = time.time()
    # last_size = 0
    # total_size = 0        # of all documents we've indexed so far
    num_postings_seen = 0

    for docID, f in enumerate(json_file_paths):
      
      # tokenize, store url for each doc, get posting info for every term in one doc, add to cur partial index
      tokens, url = self.tokenizer(f)
      self.docID_to_url[docID] = url                                      # keep track of docID to url
      dict_term_to_posting_info = self.create_postings(docID, tokens)     # for one doc

      for t in dict_term_to_posting_info:
        if t not in current_partial_index_dict:
          current_partial_index_dict[t] = [t]                               # current partial index dict: key = term, val = term string, followed by list of lists, inner list [docID_list, tf]
        current_partial_index_dict[t].append(dict_term_to_posting_info[t])  # add another list of [docID, tf] into term's list of posting info
        num_postings_seen += 1

      # get index size, print avg time it takes
      # cur_index_size = sys.getsizeof(current_partial_index_dict)    # in bytes
      # total_size += cur_index_size
      # if total_size - last_size > 10*(2**20):           # every 10 MB
      #   last_size = total_size
      #   ts = time.time()
      #   print(f"d_id: {docID}, time for last block: {ts - last_ts}, avg time per GB: {1.0 * (ts - start_time) / total_size * 2**30}", flush=True)     # 2^30 for gb 
      #   last_ts = ts

      # whenever current partial index reaches 1 million postings, write it to disk
      # sort by term, then turn lists into json strings, then write (one term's posting info per line)
      if num_postings_seen > 10**6:                                    # every 1 million postings
        file_path = f"index{self.num_partial_indexes}.txt"             # new name for index file
        self.num_partial_indexes += 1
        with open(file_path, "w") as f:
          for t in sorted(current_partial_index_dict):                 # sorts my keys alphabetically
            json_str_term = json.dumps(current_partial_index_dict[t])
            f.write(json_str_term + "\n")
        print("I wrote ", file_path)

        current_partial_index_dict = dict()                            # reset partial index bc we've dumped it to disk
        num_postings_seen = 0                                          # reset count var
    
    # store the docID_to_url dict into a text file
    with open("docID_to_url.txt", "w") as dtu:
      url_dict_str = json.dumps(self.docID_to_url)
      dtu.write(url_dict_str)

  def calc_tfidf(self, tf, N, df):
    # (1 + log(tf)) * log(N / df)
    # tf = term freq in current document
    # N = total documents (everything in corpus)
    # df = document frequency (how many documents across N the term shows up)
    return round((1 + math.log(tf)) * math.log(N / df), 3)

  def update_posting_info(self, term_posting_info):
    # input: term_posting_info is a list that resembles: ["00128", [603, 1], [857, 2]]
        # this is in form: [term, [docID1, tf], [docID2, tf2]...]
    # output: for each [docID, tf] inner list, compute tfidf to store in place of tf
        # this is in form: [term, [docID1, tfidf], [docID2, tfidf]...]
    df = len(term_posting_info) - 1                                   # df is len(postings_list), which is len(input) - 1
    for idx, inner_list in enumerate(term_posting_info[1:]):
      tfidf = self.calc_tfidf(inner_list[1], self.num_documents, df)
      term_posting_info[idx] = [inner_list[0], tfidf]                              # +1 bc we sliced off index 0 when enumerating
      #clearprint(term_posting_info)
    return term_posting_info

"""
merge_partial_indexes(dir_path)
    -- input: dir path where u can find all ur partial index files (each index file is sorted alphabetically alr by term)
    -- output: a completed index on disk, which u have an index_of_index for (byte offsets into the completed_index)

    steps:
      1) find all indexX.txt files (X >= 0)
      2) open all of these files, store their file ptrs into list
      3) create min heap that will take tuples: (term, idx_of_fileptr, term_posting_info)
        -- note: ordering within heap based on first element of tuple, aka term (so u will pop alphabetically smallest)
      4) populate heap once using readline() on every partial index
      5) pop once from heap, extract info, repopulate heap by adding another tuple
        -- note: this new tuple is constructed by readline() on the fp of the tuple we just popped from heap
      6) continue this process for cur_term, once we reach a new term, write the concatenated posting list for the cur_term to disk
        -- note: posting list will now contain [docID, tfidf], not [docID, tf], this is an intermediate step here that i'll gloss over
        -- note: this is where u wanna calc byte_offset into the complete_index
      7) once you reach eof (aka "not line" after readline()), then u don't add to heap
      8) perform above steps until heap is empty, should have completed index file on disk + index_of_index
"""

def merge_partial_indexes(self, dir_path):
    # go into dir path, find all files of name indexX.txt, where X >= 0
    files = os.listdir(dir_path)
    file_pointers = list()          # extract lines one at a time from each of these open files

    # find all partial index files, open them and add their file pointers to a list
    for f in files:
      match = re.match(r'index(\d+)\.txt', f)     # index, then (\d+) for one or more digits, captured as a group, \.txt to match ".txt", \ as escape char for the .
      if match:
        file_path = os.path.join(dir_path, f)     # Open the file and get its file pointer
        fp = open(file_path, 'r')
        file_pointers.append(fp)     # Add the file pointer to the list

    # iterate over each fp, read a line, extract the term
    # add tuple of (term, term_info)
    min_heap = []
    # populate heap
    for fp_idx, fp in enumerate(file_pointers):
      line = fp.readline()
      if line:
        term_posting_info = json.loads(line)
        term = term_posting_info.pop(0)                # don't want to store term string in index, keep it in index_of_index.txt
        term_posting_info = self.update_posting_info(term_posting_info)    # store tfidf, not tf
        #print(term_posting_info)
        tuple_data = (term, fp_idx, term_posting_info)
        heapq.heappush(min_heap, tuple_data)           # note: min_heap uses the first element of the tuple for comparisons
      else:
        print("Initial file was empty.\n")

    
    # perform merging
    # pop from min_heap, repopulate from same file
    cur_term = None        # these are strings
    last_term = None
    cur_term_info_list = list()
    term_to_byte_offset_dict = dict()

    with open("complete_index.txt", "w") as ci:
      while len(min_heap) > 0:
        alphabetically_smallest = heapq.heappop(min_heap)   # get next tuple
        cur_term, fp_idx, term_info = alphabetically_smallest
        #print(term_info)

        # repopulate heap
        line = file_pointers[fp_idx].readline()
        if line:                                  # json string
          term_posting_info = json.loads(line)
          term = term_posting_info.pop(0)
          term_posting_info = self.update_posting_info(term_posting_info)    # store tfidf, not tf
          new_tuple = (term, fp_idx, term_posting_info)
          heapq.heappush(min_heap, new_tuple)
        
        # add to cur_term_info_list
        if cur_term != last_term and last_term is not None:
          byte_offset = ci.tell()                      # where we are in the complete index in bytes
          ci.write(json.dumps(cur_term_info_list) + "\n")     # write to file
          cur_term_info_list = list()                  # reset the list
          term_to_byte_offset_dict[last_term] = byte_offset

        # for word in term_info:
        #   if type(word) == type(""):
        #     import pdb
        #     pdb.set_trace()             # auto detection of strings in complete index (not supposed to happen), enter pdb (python debugger) if we do

        cur_term_info_list += term_info                # join the lists
        last_term = cur_term
        
      # perform again, need to process last term after heap empties
      byte_offset = ci.tell()                      # where we are in the complete index in bytes
      ci.write(json.dumps(cur_term_info_list))     # write to file
      cur_term_info_list = list()                  # reset the list
      term_to_byte_offset_dict[last_term] = byte_offset
    
    # we have merged index! Now we need the index_of_index (put to new file, called index_of_index.txt)
    fname = "index_of_index.txt"
    with open(fname, "w") as f:
      json.dump(term_to_byte_offset_dict, f)
        

def generate_report(inverted_index_shelve_file, num_docs):
  fname = "REPORT.txt"
  fname2 = "InvertedIndex.txt"    # store it in a human readable format (not shelve file)

  if os.path.isfile(fname):
    os.remove(fname)
  if os.path.isfile(fname2):
    os.remove(fname2)
  
  with shelve.open(inverted_index_shelve_file, writeback=True) as my_shelve:
    with open(fname, 'w') as f:
      f.write("REPORT: \n")
      f.write("Number of indexed documents: " + str(num_docs) + ". \n")
      f.write("Number of unique words: " + str(len(my_shelve["my_shelve_dict"]) - 1) + ". \n")         # -1 bc i store "num_unique_words"
      
      file_size = os.path.getsize("dev.shelve")                                  # get size of text file
      f.write(f"Size of the inverted index: {file_size / 1024.0:.2f} KB.\n")

    with open(fname2, 'w') as f2:
      # put shelve file of inverted_index info into text file
      for term, term_posting_list in my_shelve["my_shelve_dict"].items():
        f2.write(f"{term}\n")
        for posting in term_posting_list:
          f2.write(f"{posting.docId}, {posting.tf}, {posting.position_lst}\n")
        f2.write("\n")
      

def main(mode):
  root_dir = "/home/czejda/cs121hw3/search_engine/DEV"
  ii = InvertedIndex()
  if mode == "--index":
    ii.create_and_store_partial_indexes(root_dir)
  elif mode == "--merge":
    dir_path = "."
    ii.num_documents = 55393             # hard coded for merging
    ii.merge_partial_indexes(dir_path)
  else:
    print("Unknown argument.")
  #generate_report(shelve_file, ii.docCount)

if __name__ == "__main__":
  main(sys.argv[1])
        