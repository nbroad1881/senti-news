import pathlib
import logging
import os

from dotenv import load_dotenv
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from fastai.text import load_learner

"""
models.py
---
Holds 3 sentiment classifiers: TextBlob, Vader, and LSTM.
TextBlob is pretrained on nltk IMDB data using a NaiveBayes approach.
Vader is pretrained on tweets from Twitter.
LSTM is trained using the ULMFit technique of transfer learning for NLP purposes.
The starting model is already a language model trained on wikipedia.
The language model then gets trained with 1000 articles.
Then the model becomes a classifier and gets trained on  few hundred hand-labeled news titles.
The saved model is then stored locally.

Each model has its own class and a method to evaluate a string's sentiment.
"""
load_dotenv()
logging.basicConfig(level=logging.INFO)


class LSTMAnalyzer:

    def __init__(self, model_dir=None, model_name=None):
        """
        Load a fastai.Learner object that was made by export()
        :param model_dir: Directory that holds saved model
        :type model_dir: str or Path
        :param model_name: Name of model to load
        :type model_name: str
        """
        if model_dir and model_name:
            self.model_dir = pathlib.Path(model_dir)
            self.model_name = model_name
        else:
            self.model_dir = pathlib.Path(os.environ.get("LSTM_PKL_MODEL_DIR"))
            self.model_name = os.environ.get('LSTM_PKL_FILENAME')
        try:
            self.model = load_learner(self.model_dir, self.model_name)
        except BaseException as e:
            logging.info("Failed to load LSTM model. " + str(e))

        self.name = 'lstm'

    def evaluate(self, text):
        """
        Gives the sentiment scores for the given text.
        :param text: Text to be scored for sentiment
        :type text: str
        :return: dictionary of sentiment scores
        'p_pos', 'p_neg', 'p_neu' are the probabilities of those classifications.
        :rtype: dict
        """
        # Other variables returned are unnecessary
        _, _, prob_tensor = self.model.predict(text)

        return {
            'p_pos': round(float(prob_tensor[2]), 3),
            'p_neu': round(float(prob_tensor[1]), 3),
            'p_neg': round(float(prob_tensor[0]), 3)
        }


class TextBlobAnalyzer:

    def __init__(self):
        self.nb = NaiveBayesAnalyzer()
        self.name = 'textblob'

    def evaluate(self, text):
        """
        Gives the sentiment scores for the given text using the NaiveBayes analyzer.
        :param text: Text to be scored for sentiment
        :type text: str
        :return: dictionary of sentiment scores. classification can be 'pos' or 'neg'
        p_pos and p_neg are the probabilities of those classifications.
        :rtype: dict
        """

        sentiment = TextBlob(text, analyzer=self.nb).sentiment
        return {
            'p_pos': round(sentiment.p_pos, 3),
            'p_neg': round(sentiment.p_neg, 3)
        }


class VaderAnalyzer:
    """

    """

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.name = 'vader'

    def evaluate(self, text):
        """
        Gives the sentiment scores for the given text using the Vader analyzer.
        :param text: Text to be scored for sentiment
        :type text: str
        :return: dictionary of sentiment scores.
        'p_pos', 'p_neg', 'p_neu' are the probabilities of those classifications.
        'compound' is a combined score using an unknown proprietary algorithm
        :rtype: dict
        """
        score = self.analyzer.polarity_scores(text)
        return {
            'p_pos': score['pos'],
            'p_neg': score['neg'],
            'p_neu': score['neu'],
            'compound': score['compound']
        }


def analyze_title(analyzer_iter, text):
    """
    Pass an iterable of analyzers to have each evaluate the passed text.
    Returns the scores in a dict of dicts
    :param text: text to get sentiment from
    :type text: str
    :param analyzer_iter: initialized Vader/TextBlob/LSTM Analyzer
    :type analyzer_iter: VaderAnalyzer, TextBlobAnalyzer, LSTMAnalyzer
    :return: dictionary of dictionaries. Each sub-dictionary is a dictionary
    from each analyzer's evaluate() method.
    :rtype: dict
    """
    all_scores = {}
    for func in analyzer_iter:
        scores = func.evaluate(text)
        for key in scores:
            all_scores[func.name + '_' + key] = scores[key]
    return all_scores
