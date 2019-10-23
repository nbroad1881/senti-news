import requests
import json
import pickle

"""Documentation
https://developer.nytimes.com/docs/articlesearch-product/1/routes/articlesearch.json/get
"""
url = 'https://api.nytimes.com/svc/search/v2/articlesearch.json?q=biden|sanders|warren|buttigieg|harris&api-key=nSc6ri8B5W6boFhjJ6SuYpQmLN8zQuV7'
r = json.loads(requests.get(url).text)

save = False
if save:
    with open('nyt_response', 'wb') as f:
        pickle.dump(r, f)
read = False
if read:
    with open('nyt_response', 'rb') as f:
        r = pickle.load(f)
print(r['response']['meta'])

# Response structure
# 'status'
# 'copyright'
# 'response' []
#     -> 'docs' []
#             -> ['web_url', 'snippet', 'lead_paragraph', 'abstract', 'print_page', 'source', 'multimedia',
#             'headline', 'keywords', 'pub_date', 'document_type', 'news_desk', 'section_name', 'byline',
#             'type_of_material', '_id', 'word_count', 'uri']
#     -> 'meta'