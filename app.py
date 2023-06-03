from flask import Flask, render_template, request
#from mileStone1 import posting
#from MS2 import Timer
#from MS2 import Search
import mileStone1
import mileStone2
from mileStone2 import launch_milestone_2
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def perform_search():
    query = request.args.get('query')
    all_results = perform_actual_search(query)

    # Pagination
    page = request.args.get('page', 1, type=int)
    results_per_page = 10
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    results = all_results[start_index:end_index]

    return render_template('results.html', query=query, results=results, page=page)



def perform_actual_search(query):
    # Dummy URLs for demonstratio
    dummy_urls = launch_milestone_2(query)
    if len(dummy_urls) == 0:
        dummy_urls.append("NoResults")
    
    return dummy_urls
'''
def main():
    #query = "nearli"
    index_shelve_file = "dev.shelve"
    
    
    with shelve.open(index_shelve_file, 'r') as my_shelve:    # open index shelve
        
        s = Search(my_shelve)
        while True:
            user_query = input("Search for: ")
            start_t = time.time()

            top_5_tuples = s.search_for(user_query, 5)       # list of tuples, (tfidf, docID)
            print("Your top 5 results are:")
            for tfidf, docID in top_5_tuples:
                print(f"DocID: {docID}, Tfidf: {tfidf}, URL: {s.URLs[docID]}")
            print(f"Total time was {time.time() - start_t}\n")
'''
if __name__ == '__main__':
    app.run(port=5001)
