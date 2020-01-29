import pathlib
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from fastai.text import *

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

    def train(self, language_model=None, classifier_model=None):

        """
        Training the LSTM. I ran it in a colab notebook to use their GPUs.
        :param language_model:
        :type language_model:
        :param classifier_model:
        :type classifier_model:
        :return:
        :rtype:
        """
        data_dir = pathlib.Path('training-data')
        labeled_titles_data = 'labeled-titles.csv'

        # DataBunch is used to train a Learner
        model_dir = pathlib.Path('data-bunch')

        # TextLMDataBunch can be used to train a language model
        # Save time by loading pre-existing DataBunch if one exists
        if language_model and (model_dir / language_model).isfile():
            data_lm = load_data(model_dir, language_model)
        else:
            # Create DataBunch from csv
            data_lm = TextLMDataBunch.from_csv(data_dir, 'LM-news-data.csv')

        # TextClasDataBunch can be used to train a classifier
        # Save time by loading pre-existing DataBunch if one exists
        if classifier_model and (model_dir / classifier_model).isfile():
            data_clf = load_data(model_dir, classifier_model, bs=16)
        else:
            # Create DataBunch from csv
            data_clf = TextClasDataBunch.from_csv(data_dir, labeled_titles_data, vocab=data_lm.train_ds.vocab, bs=32)

        # Training the language model
        learn_news = language_model_learner(data_lm, AWD_LSTM, drop_mult=0.5)
        # Train using one cycle policy (search for leslie smith)
        learn_news.fit_one_cycle(1, 1e-2)

        # Train everything
        learn_news.unfreeze()
        learn_news.fit_one_cycle(1, 1e-3)

        # Saving the language model
        learn_news.save_encoder(data_dir / 'ft_enc_news')

        # Use TextClasDataBunch created earlier to train a classifier
        learn_news = text_classifier_learner(data_clf, AWD_LSTM, drop_mult=0.5)
        learn_news.load_encoder(data_dir / 'ft_enc_news')

        # Training classifier
        learn_news.fit_one_cycle(1, 1e-2)

        # Set all layers except last two to un-trainable
        learn_news.freeze_to(-2)
        learn_news.fit_one_cycle(1, slice(5e-3 / 2., 5e-3))

        # Train all layers
        learn_news.unfreeze()
        learn_news.fit_one_cycle(1, slice(2e-3 / 100, 2e-3))

        learn_news.export("news-classifier.pkl")

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
