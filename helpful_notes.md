*news\_url_getter.py* is the first attempt at getting urls of news articles from CNN, NYTimes, Fox News using news-api.

*news_scrapy* contains everything need for scraping sites

*texts* are:
* text documents made by scraping news articles
* poll ratings from realclearpolitics

*urls* are csv files containing urls for articles



### Potential Problems
1. [News API](https://newsapi.org/) only gives you 260 characters of text, but it gives the URL, so potentially able to [scrape](https://towardsdatascience.com/web-scraping-news-articles-in-python-9dd605799558),[also this](https://hackernoon.com/i-made-a-news-scrapper-with-100-lines-of-python-2e1de1f28f22).
	* The API does give a lot of flexibility to get articles and links during small time windows. It only gives 100 articles at a time and 500 requests a day, which means there is a maximum of 500,000 articles that can found in one day. I can specify time ranges to prevent duplicate articles.
	* I'll have to come up with a consistent way of scraping the main text from each link.
	* I can filter results by domain (cnn, huffington post, fox, etc.). I may need to restrict where the articles are coming from.
	* Oct 11: Just using NY Times, CNN, and Fox News, here are the number of results for the following candidates over one week
		* Joe Biden: 323
		* Elizabeth Warren: 105
		* Bernie Sanders: 85
		* Pete Buttigieg: 38
		* Kamala Harris: 53
2. Certain candidates will receive more media attention which may obscure details.
3. Each news outlet will have its own bias.
2. What is the ground truth? Which poll do you trust?
2. How do you know there isn't data leakage? How do you know the articles aren't going off of the polls? (Double check dates)

### Word Representation Models
1. [Word2Vec](https://code.google.com/archive/p/word2vec/) - Google's model that can do skip-gram or bag-of-words models
2. Co-occurrence matrix -> SVD
	* LSA, HAL, COALS, 
1. [GloVe - Global Vectors for Word Representation](https://nlp.stanford.edu/projects/glove/)
	* Incorporate vector differences
	* Use ratio of co-occurrence probabilities to encode meaning components
	* Scale word vector values depending on word frequency.
4. [ELMo - Embedded Learning Models](https://allennlp.org/elmo)
	* Can handle complex characteristics of words use like syntax and semantics
	* Can handle complex context like polysemy
	* Created with Bidirectional language model
	* "Can be used for including question answering, textual entailment and sentiment analysis."
5. FastText

### Tools
1. RNNs ([bidirectional](https://towardsdatascience.com/a-beginners-guide-on-sentiment-analysis-with-rnn-9e100627c02e), deep, [LSTM](https://towardsdatascience.com/sentiment-analysis-using-lstm-step-by-step-50d074f09948), GRU)
2. [BERT - Bidirectional Encoder Representations from Transformers](https://arxiv.org/abs/1810.04805)




### Useful Resources

2. [SpaCy - Free, Powerful NLP package.](https://spacy.io/)
	* Pretrained word vectors
	* Deep learning integration
	* Named entity recogition
	* [Cheat Sheet](https://www.datacamp.com/community/blog/spacy-cheatsheet)
3. [Apache OpenNLP](https://opennlp.apache.org/)
4. [NLTK](http://www.nltk.org)
	* Corpora and lexical resources like WordNet
	*  Text processing libraries for classification, tokenization, stemming, tagging, parsing, and semantic reasoning, wrappers for industrial-strength NLP libraries 
5. [PyTorch NLP](https://pytorchnlp.readthedocs.io/en/latest/)
6. [Textacy](https://github.com/chartbeat-labs/textacy)
	* Works with SpaCy
	* Pre and post processing
7. [TextBlob](https://textblob.readthedocs.io/en/dev/)
	* part-of-speech tagging, noun phrase extraction, sentiment analysis, classification, translation


### Possible Extensions
1. Use tweets for more information