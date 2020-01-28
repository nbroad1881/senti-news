# Sentinews
This package contains craping tools and sentiment analyzers for a sentiment analysis project focused on news headlines about US presidential candidates in the 2020 election. See more at [sentimentr.nmbroad.com](sentimentr.nmbroad.com)).

## Background
I thought it would be interesting to see if trends in sentiment toward candidates could be seen in news headlines. Even though journalism is meant to be objective, small amounts of subjectivity can show up now and again. Most people know that CNN and Fox News are on opposite sides of the political viewpoint spectrum. CNN is the more liberal one and Fox the more conservative. 
 

## Sentiment Analysis Models
sentinews.models contains 3 models currently (TextBlob, VADER, LSTM), with a 4th (BERT) on the way. [TextBlob](https://textblob.readthedocs.io/en/dev/) and [Vader](https://github.com/cjhutto/vaderSentiment) are pre-existing tools with sentiment analysis functionality, and the LSTM and BERT models are trained by 

#### TextBlob
TextBlob's model is trained with an nltk NaiveBayesClassifier on IMDB data (nltk.corpus.movie_reviews). This model uses the frequency of certain words to determine the probaility of the text being positive or negative. A Naive Bayes Model works by finding the empirical probability of a piece of label having certain features, the probability of the features, and the probability of the label. These all get combined using Bayes rule to find the probability of a label given features. This is a Naive approach because it assumes all the features are independent.

![Bayes rule](https://raw.githubusercontent.com/nbroad1881/senti-news/master/assets/equation.svg?sanitize=true <src="https://raw.githubusercontent.com/nbroad1881/senti-news/master/assets/equation.svg?sanitize=true"> "Naive Bayes equation")


### VADER
VADER's model is a lexicon approach using social media posts from Twitter. It is capable of understanding emoticons (e.g. :-) ), punctuation (!!!), slang (nah) and popular acronyms (LOL).  ~9,000 token features were rated using multiple human judges on an integer scale from -4 (extremely negative) to +4 (extremely positive).

### LSTM
The LSTM model is built by me and follows the [Universal Language Model Fine-tuning (ULMFiT) technique used by Jeremy Howard.](https://arxiv.org/abs/1801.06146) It is essentially the equivalent of transfer learning in computer vision.  It starts with a well-trained language model, such as the [AWD-LSTM](https://arxiv.org/abs/1708.02182), and then it trains it's language model on news-related text.  The model then get's trained for sentiment analysis on news headlines. The hope is that there is fundamental language understanding in the base models and the last layers help it understand the specific task of gauging sentiment in news headlines.

### BERT
Though not implemented here yet, BERT is the first prominent model using a transformer architecture.  Transformers enable text understanding of an entire sentence at once, rather than the sequential nature of RNNs and LSTMs. In that sense, they are considered bi-directional (the B in BERT), and some might argue there is no direction any more.   

## Scraping Tools
The scraping tools are essentially wrappers for the APIs of CNN, The New York Times, and Fox News. There is additional support for NewsAPI to get even more headlines, but to constrain the problem initially, just those main three are used. NewsAPI does make it convenient to get recent headlines, but the free account can only search 30 days in the past. Searching beyond that requires the other APIs.


