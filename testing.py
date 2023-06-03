import sys
import nltk
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import os
import json
import openai

# testing getsizeof()
# conclusion: it's not what i want :(, used another method to get byte offsets
d = [
    {"id": 1, "name": "Object 1", "value": 10},
    {"id": 2, "name": "Object 2", "value": 20},
    {"id": 3, "name": "Object 3", "value": 30}, # up until here it's 80
    {"id": 3, "name": "Object 3", "value": 30}  # add this line, becomes 88
]
#print(sys.getsizeof(d))

# what are the english stopwords?
#nltk.download('stopwords')
#stop_words = set(stopwords.words('english'))
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
#print(stemmed_stop_words)


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


# def clean_html(html):
#     soup = BeautifulSoup(html, 'html.parser')
    
#     # Remove unwanted elements
#     for element in soup(['script', 'style', 'head', 'title', 'meta', '[document]']):
#         element.extract()
    
#     # Extract visible text
#     visible_text = soup.get_text(separator=' ')
    
#     # Clean up extra whitespace and newlines
#     visible_text = ' '.join(visible_text.split())
    
#     return visible_text

# bad_html = '<html> <head><title>Example Page</title></head><body><h1>Hello, World!</h1><p>This is an example paragraph.</p><script>alert("This script should be removed.");</script></body></html>'

# print("\n" + clean_html(bad_html) + "\n")

from lxml.html.clean import Cleaner


def sanitize(dirty_html):
    cleaner = Cleaner(page_structure=True,
                  meta=True,
                  embedded=True,
                  links=True,
                  style=True,
                  processing_instructions=True,
                  inline_style=True,
                  scripts=True,
                  javascript=True,
                  comments=True,
                  frames=True,
                  forms=True,
                  annoying_tags=True,
                  remove_unknown_tags=True,
                  safe_attrs_only=True,
                  safe_attrs=frozenset(['src','color', 'href', 'title', 'class', 'name', 'id']),
                  remove_tags=('span', 'font', 'div')
                  )

    return cleaner.clean_html(dirty_html)

bad_html = '"\n\n\n\n<!DOCTYPE HTML PUBLIC \\\"-//W3C//DTD HTML 4.01 Transitional//EN\\\">\n<html>\n<head>\n<title>UCI Machine Learning Repository: Horse Colic Data Set: Support</title>\n\n<!-- Stylesheet link -->\n<link rel=\"stylesheet\" type=\"text/css\" href=\"../assets/ml.css\" />\n\n<script language=\"JavaScript\" type=\"text/javascript\">\n<!--\nfunction checkform ( form )\n{\n  // see http://www.thesitewizard.com/archive/validation.shtml\n  // for an explanation of this script and how to use it on your\n  // own website\n\n  // ** START **\n  if (form.q.value == \"\")\n  {\n    alert( \"Please enter search terms.\" );\n    form.q.focus();\n    return false ;\n  }\n\n  if (getCheckedValue(form.sitesearch) == \"ics.uci.edu\" && form.q.value.indexOf(\"site:archive.ics.uci.edu/ml\") == -1)\n  {\n    form.q.value = form.q.value + \" site:archive.ics.uci.edu/ml\";\n  }\n\n  // ** END **\n  return true ;\n}\n\n// return the value of the radio button that is checked\n// return an empty string if none are checked, or\n// there are no radio buttons\nfunction getCheckedValue(radioObj) {\n\tif(!radioObj)\n\t\treturn \"\";\n\tvar radioLength = radioObj.length;\n\tif(radioLength == undefined)\n\t\tif(radioObj.checked)\n\t\t\treturn radioObj.value;\n\t\telse\n\t\t\treturn \"\";\n\tfor(var i = 0; i < radioLength; i++) {\n\t\tif(radioObj[i].checked) {\n\t\t\treturn radioObj[i].value;\n\t\t}\n\t}\n\treturn \"\";\n}\n//-->\n</script>\n\n</head>\n\n<body>\n\n\n<!-- SITE HEADER (INCLUDES LOGO AND SEARCH BOX) -->\n\n<table width=100% bgcolor=\"#003366\">\n<tr>\n\t<td>\n\t\t<span class=\"normal\"><a href=\"../index.html\" \nalt=\"Home\"><img src=\"../assets/logo.gif\" \nborder=0></img></a><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"http://cml.ics.uci.edu\"><font color=\"FFDD33\">Center for Machine Learning and Intelligent Systems</font></a></span>\n\t</td>\n\t<td width=100% valign=top align=\"right\">\n\t\t<span class=\"whitetext\">\n\t\t<a href=\"../about.html\">About</a>&nbsp;\n\t\t<a href=\"../citation_policy.html\">Citation Policy</a>&nbsp;\n\t\t<a href=\"../donation_policy.html\">Donate a Data Set</a>&nbsp;\n\t\t<a href=\"../contact.html\">Contact</a>\n\t\t</span>\n\n\t\t<br>\n\t\t<br>\n\t\t<!-- Search Google -->\n\n\t\t<FORM method=GET action=http://www.google.com/custom onsubmit=\"return checkform(this);\">\n\t\t<INPUT TYPE=text name=q size=30 maxlength=255 value=\"\">\n\t\t<INPUT type=submit name=sa VALUE=\"Search\">\n\t\t<INPUT type=hidden name=cof VALUE=\"AH:center;LH:130;L:http://archive.ics.uci.edu/assets/logo.gif;LW:384;AWFID:869c0b2eaa8d518e;\">\n\t\t<input type=hidden name=domains value=\"ics.uci.edu\">\n\t\t<br>\n\t\t<input type=radio name=sitesearch value=\"ics.uci.edu\" checked> <span class=\"whitetext\"><font size=\"1\">Repository</font></span>\n\t\t<input type=radio name=sitesearch value=\"\"> <span class=\"whitetext\"><font size=\"1\">Web</font></span>\n\t\t&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n\t\t<A HREF=http://www.google.com/search><IMG SRC=http://www.google.com/logos/Logo_25blk.gif border=0 ALT=Google align=middle height=27></A>\n\t\t<br>\n\t\t</FORM>\n\t\t<!-- Search Google -->\n\n\n\t\t<span class=\"whitetext\"><a href=\"../datasets.php\"><font size=\"3\" color=\"#FFDD33\"><b>View ALL Data Sets</b></font></a></span>\n\t\t<br>\n\t</td>\n</tr>\n</table>\n\n<br />\n<table width=100% border=0 cellpadding=2><tr><td>\n\n\n   <table><tr>\n     <td valign=top>\n\t<p>\n\t<span class=\"heading\"><b>Horse Colic Data Set</b></span>\n\n\t\t\n\t\t<img src=\"../assets/MLimages/Large47.jpg\" hspace=20 vspace=10 align=right />\t\t<p class=\"normal\">Below are papers that cite this data set, with context shown.\n\t\tPapers were automatically harvested and associated with this data set, in collaboration with <a href=\"http://rexa.info\">Rexa.info</a>.</p>\n\t\t<img src=\"../assets/rexa.jpg\" />\n\t\t<p class=\"normal\"><a href=\"/ml/datasets/Horse+Colic\">Return to Horse Colic data set page</a>.\n\t\t<hr><p class=\"normal\"><a name=\"09b1c64b200c3b3acff18a3e45a2d75ba0aef2b7\"></a><i>Julie Greensmith. <a href=\"http://rexa.info/paper/09b1c64b200c3b3acff18a3e45a2d75ba0aef2b7\">New Frontiers For An Artificial Immune System</a>. Digital Media Systems Laboratory HP Laboratories Bristol. 2003. </i><br><br>with a 1 and the absence of that word is marked with a 0. This gives rise to the creation of the feature vectors for use within the classifier. For example, our most informative words from the tiny dataset above were <b>horse</b> and monitor. So, the feature vector for the document D containing the words \"I rode a horse today\" would look like \"1 0\", thus denoting the presence of the word horse within the<br></p><hr><p class=\"normal\"><a name=\"a914c3920de02d035db122f72172f31446e9f5e1\"></a><i>Richard Nock and Marc Sebban and David Bernard. <a href=\"http://rexa.info/paper/a914c3920de02d035db122f72172f31446e9f5e1\">A SIMPLE LOCALLY ADAPTIVE NEAREST NEIGHBOR RULE WITH APPLICATION TO POLLUTION FORECASTING</a>. International Journal of Pattern Recognition and Artificial Intelligence Vol. 2003. </i><br><br>section. The justification for the better choice of the additional neighbors in the k-sNN algorithm is now visually evident from Fig. 2, when looking at the \u00b5(k) curves. For the <b>Horse</b> <b>Colic</b> dataset, the curve of the sNN rule is clearly located over the two other curves. For particular points of 45 # \u00b5(k) # 60, the accuracies of the NN and tNN rules are similar, but they are beaten by the sNN<br></p><hr><p class=\"normal\"><a name=\"1b77c2b6fd8a261af286cf411879f9f520824bd6\"></a><i>Marc Sebban and Richard Nock and St\u00e9phane Lallich. <a href=\"http://rexa.info/paper/1b77c2b6fd8a261af286cf411879f9f520824bd6\">Stopping Criterion for Boosting-Based Data Reduction Techniques: from Binary to Multiclass Problem</a>. Journal of Machine Learning Research, 3. 2002. </i><br><br>a weighted decision rule provides better results than the unweighted rule. Among them, 7 datasets (Balance, Echocardiogram, German, <b>Horse</b> <b>Colic</b>  Led, Pima and Vehicle) see important improvements, ranging from 1% to } 5%. In contrast, only one dataset sees significant accuracy decrease (Car,<br></p><hr><p class=\"normal\"><a name=\"a32ab1b3da96c9ae515a685b4fcf50e857708f24\"></a><i>Mukund Deshpande and George Karypis. <a href=\"http://rexa.info/paper/a32ab1b3da96c9ae515a685b4fcf50e857708f24\">Using conjunction of attribute values for classification</a>. CIKM. 2002. </i><br><br>We performed our experiments using a 10 way cross validation scheme and computed average accuracy across different runs. We ran our experiments using a support threshold of 1.0% for all the datasets, except hepati, <b>horse</b> where we used a support threshold of 2.0% and for lymph and zoo we used the support threshold of 5.0%. This was done to ensure that the composite features generated are<br></p><hr><p class=\"normal\"><a name=\"e69241ee87f9d58fd07b8ccbee48fbaa881fd695\"></a><i>Huan Liu and Hiroshi Motoda and Lei Yu. <a href=\"http://rexa.info/paper/e69241ee87f9d58fd07b8ccbee48fbaa881fd695\">Feature Selection with Selective Sampling</a>. ICML. 2002. </i><br><br>2 and 3 in Table 2) by simply treating them as continuous. The results are reported in Table 5. ReliefS works as well as or better than ReliefF except for 3 cases (some particular bucket sizes for data sets PrimaryTumor, Zoo, <b>Colic</b> . The detailed re0.95 0.955 0.96 0.965 0.97 0.975 0.98 0.985 0.99 0.995 1 102030405060708090100 Precision Percentage by bucket size from 7 to 1 ReliefS ReliefF 0.95 0.955<br></p><hr><p class=\"normal\"><a name=\"70172e511a3bc27c7927119a3b2a3405fbad99e0\"></a><i>Kai Ming Ting and Ian H. Witten. <a href=\"http://rexa.info/paper/70172e511a3bc27c7927119a3b2a3405fbad99e0\">Issues in Stacked Generalization</a>. J. Artif. Intell. Res. (JAIR, 10. 1999. </i><br><br>C4.5 NB IB1 1 0.36 0.20 0.42 0.63 0.30 0.04 2 0.39 0.19 0.41 0.65 0.28 0.07 C4.5 for ff 1 ; NB for ff 2 ; IB1 for ff 3 . Table 5: (a) Weights generated by MLR (model ~ M 0 ) for the <b>Horse</b> and Credit datasets. Splice Abalone Waveform Class C4.5 NB IB1 C4.5 NB IB1 C4.5 NB IB1 1 0.23 0.43 0.36 0.25 0.25 0.39 0.16 0.59 0.34 2 0.15 0.72 0.12 0.27 0.20 0.25 0.14 0.72 0.07 3 0.08 0.52 0.40 0.30 0.18 0.39 0.04<br></p><hr><p class=\"normal\"><a name=\"cd11168bb19fd462bc59beefbe670bc4eb31e3eb\"></a><i>Mark A. Hall. <a href=\"http://rexa.info/paper/cd11168bb19fd462bc59beefbe670bc4eb31e3eb\">Department of Computer Science Hamilton, NewZealand Correlation-based Feature Selection for Machine Learning</a>. Doctor of Philosophy at The University of Waikato. 1999. </i><br><br>examples described by 35 nominal features. Features measure properties of leaves and various plant abnormalities. There are 19 classes (diseases). <b>Horse</b> <b>colic</b> (hc) There are 368 instances in this dataset, provided by Mary McLeish and Matt Cecile from the University of Guelph. There are 27 attributes, of which 7 are continuous. Features include whether a horse is young or old, whether it had surgery,<br></p><hr><p class=\"normal\"><a name=\"27e33344198975ea1b20e02c8f0fce01cd29f6e5\"></a><i>Eibe Frank and Ian H. Witten. <a href=\"http://rexa.info/paper/27e33344198975ea1b20e02c8f0fce01cd29f6e5\">Generating Accurate Rule Sets Without Global Optimization</a>. ICML. 1998. </i><br><br>has classes 1 and 3 combined and classes 4 to 7 deleted, and the <b>horse</b> <b>colic</b> dataset has attributes 3, 25, 26, 27, 28 deleted with attribute 24 being used as the class. We also deleted all identifier attributes from the datasets. 4 We used Revision 8 of C4.5. Table 2: Experimental<br></p><hr><p class=\"normal\"><a name=\"287f8092a743949a6e0151893b9e3bc4d03466ed\"></a><i>Gabor Melli. <a href=\"http://rexa.info/paper/287f8092a743949a6e0151893b9e3bc4d03466ed\">A Lazy Model-Based Approach to On-Line Classification</a>. University of British Columbia. 1989. </i><br><br>were: echocardiogram, hayes-roth, heart, <b>horse</b> <b>colic</b> andiris datasets. These datasets (marked in Table 7.1 with a * symbol beside their name) contain a sampling of attribute types and domains. For this initial study however the datasets needed to be small enough (#<br></p><hr><p class=\"normal\"><a name=\"cf334aad055b27faaeece97ee1630e146388cd10\"></a><i>H. Altay G uvenir and Aynur Akkus. <a href=\"http://rexa.info/paper/cf334aad055b27faaeece97ee1630e146388cd10\">WEIGHTED K NEAREST NEIGHBOR CLASSIFICATION ON FEATURE PROJECTIONS</a>. Department of Computer Engineering and Information Science Bilkent University. </i><br><br>row of each k value presents the accuracy of the WkNNFP algorithm with equal feature weigths, while the second row shows the accuracy obtained by WkNNFP using Table 1: Comparison on some real-world datasets. Data Set: cleveland glass <b>horse</b> hungarian iris liver sonar wine No. of Instances 303 214 368 294 150 345 208 178 No. of Features 13 9 22 13 4 6 60 13 No. of Classes 2 6 2 2 3 2 2 3 No. of Missing<br></p><hr><p class=\"normal\"><a name=\"939595ca638eb3390e9bb9c4e6cc1352163cbf18\"></a><i>Kai Ming Ting and Ian H. Witten. <a href=\"http://rexa.info/paper/939595ca638eb3390e9bb9c4e6cc1352163cbf18\">Stacked Generalization: when does it work</a>. Department of Computer Science University of Waikato. </i><br><br>2 -- 0.00 0.93 0.01 0.00 0.00 0.07 Table 8: Ave. error rates of BestCV, Majority Vote and MLR (model ~ M 0 ), along with the standard error (#SE) between BestCV and the worst level-0 generalizers. Dataset #SE BestCV Majority MLR <b>Horse</b> 0.5 17.1 15.0 15.2 Splice 2.5 4.5 4.0 3.8 Abalone 3.3 40.1 39.0 37.9 Led24 8.7 32.8 31.8 32.1 Credit 8.9 17.4 16.1 16.2 Nettalk(s) 10.8 12.7 12.2 11.5 Coding 12.7 25.0<br></p><hr><p class=\"normal\"><a name=\"e2b2b723df700c90e69a31a4403b740c2d2a7b2f\"></a><i>Alexander K. Seewald. <a href=\"http://rexa.info/paper/e2b2b723df700c90e69a31a4403b740c2d2a7b2f\">Dissertation Towards Understanding Stacking Studies of a General Ensemble Learning Scheme ausgefuhrt zum Zwecke der Erlangung des akademischen Grades eines Doktors der technischen Naturwissenschaften</a>. </i><br><br>breast-w Compressed glyph visualization for dataset <b>colic</b> Compressed glyph visualization for dataset credit-a Compressed glyph visualization for dataset credit-g Compressed glyph visualization for dataset diabetes Compressed glyph visualization for<br></p><hr><p class=\"normal\"><a name=\"0a882383e36d72c5890e2d191326433e23e53c9b\"></a><i>James J. Liu and James Tin and Yau Kwok. <a href=\"http://rexa.info/paper/0a882383e36d72c5890e2d191326433e23e53c9b\">An Extended Genetic Rule Induction Algorithm</a>. Department of Computer Science Wuhan University. </i><br><br>has classes 1 and 3 combined and classes 4 to 7 deleted, and the <b>horse</b> <b>colic</b> dataset has attributes 3, 25, 26, 27, 28 deleted and with attribute 24 being used as the class label. We also deleted all identifier attributes from the datasets. Table 1: Datasets used in the experiments.<br></p>\n\n\n\t</td></tr></table>\n\n\n\n<hr>\n\n<p class=\"normal\"><a href=\"/datasets/Horse+Colic\">Return to Horse Colic data set page</a>.\n\n\n<table cellpadding=5 align=center><tr valign=center>\n\t\t<td><p class=\"normal\">Supported By:</p></td>\n        <td><img src=\"../assets/nsfe.gif\" height=60 /> </td>\n        <td><p class=\"normal\">&nbsp;In Collaboration With:</p></td>\n        <td><img src=\"../assets/rexaSmall.jpg\" /></td>\n</tr></table>\n\n<center>\n<span class=\"normal\">\n<a href=\"../about.html\">About</a>&nbsp;&nbsp;||&nbsp;\n<a href=\"../citation_policy.html\">Citation Policy</a>&nbsp;&nbsp;||&nbsp;\n<a href=\"../donation_policy.html\">Donation Policy</a>&nbsp;&nbsp;||&nbsp;\n<a href=\"../contact.html\">Contact</a>&nbsp;&nbsp;||&nbsp;\n<a href=\"http://cml.ics.uci.edu\">CML</a>\n</span>\n</center>\n\n\n\n\n</body>\n</html>\n"'

#print("\n" + sanitize(bad_html).get_text() + "\n")

def get_gpt_summary():
  openai.api_key = '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'
  file_path = "/home/czejda/cs121hw3/search_engine/test_gpt.txt"
  with open(file_path, "r") as f:
      doc_text = f.read()

  messages_summary = [  {"role": "system", "content": "give a two sentence summary for this text: " + doc_text}  ]
  summary_json_str = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages = messages_summary)
  s_dict = json.loads(summary_json_str)

  real_summary = s_dict["choices"][0]["message"]["content"]
  return real_summary

print(get_gpt_summary())
# print(t)
# print("_______________________________________________")
# print(s)


title_json_str = """{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "Comparison of Master Degrees in ICS",
        "role": "assistant"
      }
    }
  ],
  "created": 1685760507,
  "id": "chatcmpl-7NBbX1gau1DSGAAMeA9f0mt84Ye4k",
  "model": "gpt-3.5-turbo-0301",
  "object": "chat.completion",
  "usage": {
    "completion_tokens": 7,
    "prompt_tokens": 1067,
    "total_tokens": 1074
  }
}"""

summary_json_str = """{
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "This text provides a comparison between 10 different Master's degree programs offered at the University of California, Irvine's Donald Bren School of Information and Computer Sciences. The programs differ in terms of focus, target population, target careers, attendance, units/courses, time to degree, tuition, financial aid, schedule, exit requirements, GRE/TOEFL requirements, career development, and contact information. The programs include Master of Science in Computer Science, Master of Science in Networked Systems, Master of Science in Software Engineering, Master of Science in Informatics, Master of Science in Statistics, Master of Computer Science, Master of Data Science, Master of Embedded and Cyber-physical Systems, Master of Software Engineering, and Master of Human-Computer Interaction and Design.",
        "role": "assistant"
      }
    }
  ],
  "created": 1685760509,
  "id": "chatcmpl-7NBbZvCqaJ6yRX1GnxtskXQtZUIkG",
  "model": "gpt-3.5-turbo-0301",
  "object": "chat.completion",
  "usage": {
    "completion_tokens": 151,
    "prompt_tokens": 1067,
    "total_tokens": 1218
  }
}"""

# new_t = json.loads(title_json_str)
# new_s = json.loads(summary_json_str)

# real_title = new_t["choices"][0]["message"]["content"]
# real_summary = new_s["choices"][0]["message"]["content"]

# print("x")



#print('\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x1eThis resource fork intentionally left blank   \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1c\x00\x1eÿÿ\n'.trim())