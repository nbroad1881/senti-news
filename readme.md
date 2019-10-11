## This repository is for my project using text data from news articles to predict the popularity of presidential candidates in the 2020 United States Presidential Election.


### What
The goal of this project is to predict the popularity of each candidate.  As of October 1, there are 19 Democrats and 4 Republicans in contention for the presidential nomination. Other parties and candidates may be considered in the future as an extension.

### How
* Use news text data to predict popularity of presidential candidates in the United States 2020 election. The news sources will have different biases and based in different regions. Initial approaches can just use lexicons, tokenization, and other rule-based approaches. Next, sentiment analysis and other NLP techniques will be used to determine whether articles are positive or negative.

#### Possible approaches
1.  Continuous bag of words, count vectorization, tokenization
2.  Naive Bayes

* I will first use a news API to gather large amounts of text data from various sources.
* The predictions will be compared against polls from the Economist/YouGov, Monmouth, Politico/Morning Consult, Harvard-Harris, Emerson, and Quinnipia.

### Why
* It is generally regarded as very difficult to predict the popularity of a presidential candidate, and it could be useful for the candidate or active supporters to know what makes a candidate’s popularity increase.


### Goals
1.	Create a pipeline to take text data from the news sources, clean the text data, and then analyze it using lexicons, tokenization, and other rule-based approaches.
2.	Start with just the top 5 democratic candidates right now (Biden, Warren, Sanders, Buttigieg, Harris)
3.	Build more complicated models that account for the news outlet’s bias, using NLP approaches like sentiment analysis, vectorization, and machine learning algorithms.
4.	Have an interactive user-facing product to show latest results.


### Potential Problems
1. [News API](https://newsapi.org/) only gives you 260 characters of text, but it gives the URL, so potentially able to [scrape](https://towardsdatascience.com/web-scraping-news-articles-in-python-9dd605799558),[also this](https://hackernoon.com/i-made-a-news-scrapper-with-100-lines-of-python-2e1de1f28f22).
2. Certain candidates will receive more media attention which may obscure details.
3. Each news outlet will have its own bias.
2. What is the ground truth? Which poll do you trust?
2. How do you know there isn't data leakage? How do you know the articles aren't going off of the polls? (Double check dates)




### Useful Resources
1. [GloVe - Global Vectors for Word Representation](https://nlp.stanford.edu/projects/glove/)
2. [SpaCy - Free, Powerful NLP package.](https://spacy.io/)
	* Pretrained word vectors
	* Deep learning integration
	* Named entity recogition
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
