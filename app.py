from flask import Flask, render_template, request
from MS1_v2 import InvertedIndex    
from MS2_v2 import Search
import time

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def perform_search():
    query = request.args.get('query')
    all_results = perform_actual_search(str(query))        # called every time we 

    # Pagination
    page = request.args.get('page', 1, type=int)
    results_per_page = 10
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    results = all_results[start_index:end_index]           # slices results list

    return render_template('results.html', query=query, results=results, page=page, num_remaining=len(all_results)-end_index)



def perform_actual_search(query):
    # Dummy URLs for demonstration
    s = Search()
    top_5_tuples = s.search_for(query, 20)       # list of tuples, (tfidf, docID)

    res = list()
    #res.append("Your top 5 results are:")
    for tfidf, docID in top_5_tuples:
        #res.append(f"DocID: {docID}, Tfidf: {tfidf}, URL: {s.urls_dict[str(docID)]}")
        res.append(s.urls_dict[str(docID)])
        print(s.urls_dict[str(docID)])
    return res

if __name__ == '__main__':
    app.run(debug=True)