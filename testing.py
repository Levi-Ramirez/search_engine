import sys
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import os
import json

# testing getsizeof()
# conclusion: it's not what i want :(, used another method to get byte offsets
d = [
    {"id": 1, "name": "Object 1", "value": 10},
    {"id": 2, "name": "Object 2", "value": 20},
    {"id": 3, "name": "Object 3", "value": 30}, # up until here it's 80
    {"id": 3, "name": "Object 3", "value": 30}  # add this line, becomes 88
]
print(sys.getsizeof(d))

# what are the english stopwords?
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
#print(stop_words)

stop_words = {'o', 'her', 'this', 'while', 'that', "haven't", 've', "isn't", 
                           'my', 'shan', 'as', "wasn't", 'so', 'how', 'did', 'herself', 'its', 
                           'further', 's', 't', 'doesn', 'when', "you've", 'some', "she's", 
                           'now', "couldn't", 'had', 'to', 'just', "didn't", 'own', 'above', 
                           'below', 'be', 'most', 'yourselves', 'in', 'between', 'will', 'can', 
                           "hasn't", 'about', 'do', "aren't", 'i', 'ourselves', "you're", 
                           "should've", 'hers', 'same', 'all', 'and', 'wasn', 'each', 'm', 
                           'doing', 'you', 'were', 'than', 'myself', 'off', 'we', 'after', 
                           'up', 'does', 'should', 'those', 'been', 'she', 'have', 'the', 
                           "mightn't", 'ma', 'because', 'by', 'they', "you'd", 'having', 
                           'into', 'mightn', 'then', "mustn't", 'has', 'is', 'down', 'shouldn', 
                           "that'll", 'am', 'yourself', 'y', 'on', 'during', 'at', 'being', 
                           'here', 're', 'over', 'too', 'if', 'where', 'isn', 'a', "needn't", 
                           'why', 'or', 'such', 'few', 'are', 'very', "it's", 'which', "hadn't", 
                           'no', 'couldn', 'before', 'itself', 'won', 'weren', 'from', 'yours', 
                           'him', 'these', 'was', 'of', 'himself', 'only', 'out', 'against', 
                           'once', 'any', 'he', 'both', 'more', "shan't", 'don', 'but', 'ours', 
                           "shouldn't", 'needn', 'through', 'again', 'd', 'what', 'for', 'ain', 
                           'until', 'll', "don't", "doesn't", 'with', "wouldn't", 'their', 'aren', 
                           'who', 'nor', 'his', 'me', 'it', 'whom', 'themselves', 'wouldn', 
                           'theirs', 'our', "won't", 'mustn', 'hadn', "you'll", 'your', 'them', 
                           'other', 'hasn', "weren't", 'haven', 'there', 'under', 'not', 'an', 'didn'}
stemmer = PorterStemmer()
stemmed_stop_words = set(stemmer.stem(word) for word in stop_words)
print(stemmed_stop_words)


def get_json_file_paths(root_dir):
    json_paths = []
    for cur_dir, all_dirs, all_files in os.walk(root_dir):     # os.walk() traverses a directory tree using DFS, iterating over all files and directories in it
      for f in all_files:
        if f.endswith(".json"):
          json_paths.append(os.path.join(cur_dir, f))
    #num_documents = len(json_paths)
    return json_paths #[:10]

def save_json_file_paths():
    root_dir = "/home/czejda/cs121hw3/search_engine/DEV"
    json_file_paths = get_json_file_paths(root_dir)
    with open("file_paths.txt", "w") as fps:               # index of each file path = docID
        json.dump(json_file_paths, fps)

save_json_file_paths()