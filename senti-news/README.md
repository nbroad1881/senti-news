# Sentinews
This package contains craping tools and sentiment analyzers for a sentiment analysis project focused on news headlines about US presidential candidates in the 2020 election. See more at ([sentimentr.nmbroad.com](sentimentr.nmbroad.com)).

## Background
I thought it would be interesting to see if trends in sentiment toward candidates could be seen in news headlines. Even though journalism is meant to be objective, small amounts of subjectivity can show up now and again. Most people know that CNN and Fox News are on opposite sides of the political viewpoint spectrum. CNN is the more liberal one and Fox the more conservative. 
 

## Sentiment Analysis Models
sentinews.models contains 3 models currently (TextBlob, VADER, LSTM), with a 4th (BERT) on the way. [TextBlob](https://textblob.readthedocs.io/en/dev/) and [Vader](https://github.com/cjhutto/vaderSentiment) are pre-existing tools with sentiment analysis functionality, and the LSTM and BERT models are trained by me.

#### TextBlob
TextBlob's model is trained with an nltk NaiveBayesClassifier on IMDB data (nltk.corpus.movie_reviews). This model uses the frequency of certain words to determine the probaility of the text being positive or negative. A Naive Bayes Model works by finding the empirical probability of a piece of label having certain features, the probability of the features, and the probability of the label. These all get combined using Bayes rule to find the probability of a label given features. 
While news headlines and movie reviews should be quite different, a movie review does contain the reviewers feelings about what they thought of the movie. That is, there is some overlap between the language used to express positive and negative emotions in both.




### VADER
[VADER's model](https://github.com/cjhutto/vaderSentiment) is a lexicon approach using social media posts from Twitter. It trained to understanding emoticons (e.g. :-) ), punctuation (!!!), slang (nah) and popular acronyms (LOL). In the context of this project, the headlines will, most likely, not contain emoticons, slang or popular acronyms; however, this model sure to gauge some level of emotion in the texts.  

### LSTM
The LSTM model is built by me and follows the [Universal Language Model Fine-tuning (ULMFiT) technique used by Jeremy Howard.](https://arxiv.org/abs/1801.06146) It is essentially the equivalent of transfer learning in computer vision.  It starts with a well-trained language model, such as the [AWD-LSTM](https://arxiv.org/abs/1708.02182), and then it trains it's language model on news-related text. The model then get's trained for sentiment analysis on news headlines. I personally hand-labeled hundreds of articles. The hope is that there is fundamental language understanding in the base models and the last layers help it understand the specific task of gauging sentiment in news headlines. Moreover, this method requires very little supervised training on my part, making it ideal.

### BERT
Though not implemented here yet, BERT is the first prominent archtecture using a transformer architecture.  Transformers enable text understanding of an entire sentence at once, rather than the sequential nature of RNNs and LSTMs. In that sense, they are considered bi-directional (the B in BERT), and the transformer is trained by guessing the missing word in a sentence, that is, looking one direction from the word and also a second, opposite direction.

## Scraping Tools
The scraping tools are essentially wrappers for the APIs of CNN, The New York Times, and Fox News. There is additional support for `NewsAPI`  to get even more headlines from other sources, but to constrain the problem initially, just those main three are used. NewsAPI does make it convenient to get recent headlines, but the free account can only search 30 days in the past. Searching beyond that requires the other APIs.

The scrapers are implemented in `Scrapy`, but that is only necessary for scraping the text body from the article. If just the headlines are desired, `requests` would be sufficient.


## Usage
This package makes use of multiple environment variables to connect to the database. Here are the fields that need to be filled in:

```
DB_DIALECT=
DB_USERNAME=
DB_PASSWORD=
DB_ENDPOINT=
DB_PORT=
DB_NAME=
DB_URL=${DB_DIALECT}://${DB_USERNAME}:${DB_PASSWORD}@${DB_ENDPOINT}:${DB_PORT}/${DB_NAME}

DB_TABLE_NAME=

NEWS_API_KEY=

LSTM_PKL_MODEL_DIR=
LSTM_PKL_FILENAME=
```
The only supported LSTM model type is a [`fastai.Learner` model](https://docs.fast.ai/basic_train.html#Learner) that has been exported using the [export function](https://docs.fast.ai/basic_train.html#Learner.export) into a `.pkl` file. 