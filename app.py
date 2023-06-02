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
    all_results, search_time = perform_actual_search(str(query))        # called every time we 
    #print(all_results)
    #print(total_time)

    # Pagination
    page = request.args.get('page', 1, type=int)
    results_per_page = 10
    start_index = (page - 1) * results_per_page
    end_index = start_index + results_per_page
    results = all_results[start_index:end_index]           # slices results list

    return render_template('results.html', query=query, results=results, page=page, num_remaining=len(all_results)-end_index, search_time=search_time)



def perform_actual_search(query):
    # Dummy URLs for demonstration
    s = Search()
    start_t = time.time()
    top_5_tuples = s.search_for(query, 20)       # list of tuples, (tfidf, docID)
    end_t = time.time()

    res = list()
    #res.append("Your top 5 results are:")
    for tfidf, docID in top_5_tuples:
        #res.append(f"DocID: {docID}, Tfidf: {tfidf}, URL: {s.urls_dict[str(docID)]}")
        res.append(s.urls_dict[str(docID)])
        print(s.urls_dict[str(docID)])
    search_time_ms = (end_t-start_t) * 1000         # end_time and start_time times are floats, float/int is double (basically float)
    search_time_ms_str = f"{search_time_ms:.0f}"    # .0f = 0 digits after decimal in floating point
    return res, search_time_ms_str

if __name__ == '__main__':
    app.run(debug=True)