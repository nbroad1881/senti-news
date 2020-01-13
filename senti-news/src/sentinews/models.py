import pathlib

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


class LSTMAnalyzer:
    """

    """

    def __init__(self, model_dir, model_name):
        """

        :param model_dir:
        :param model_name:
        """
        if model_dir is None:
            raise
        else:
            self.model_dir = pathlib.Path(model_dir)
        if model_name is None:
            raise
        else:
            self.model_name = model_name
        self.model = load_learner(self.model_dir, model_name)

    def evaluate(self, text):
        """

        :param text:
        :return:
        """
        category, num_tensor, prob_tensor = self.model.predict(text)

        return {
            'category': str(category),
            'num': int(num_tensor),
            'p_pos': round(float(prob_tensor[2]), 3),
            'p_neu': round(float(prob_tensor[1]), 3),
            'p_neg': round(float(prob_tensor[0]), 3)
        }


class TextBlobAnalyzer:
    """

    """

    def __init__(self):
        self.nb = NaiveBayesAnalyzer()

    def evaluate(self, text, all_scores=True, naive=True):
        """

        :param text:
        :param all_scores:
        :param naive:
        :return:
        """
        if naive:
            return self.nb_evaluate(text, all_scores=all_scores)

        sentiment = TextBlob(text).sentiment
        if all_scores:
            return dict(polarity=round(sentiment.polarity, 3), subjectivity=round(sentiment.subjectivity, 3))
        return dict(polarity=round(sentiment.polarity, 3))

    def nb_evaluate(self, text, all_scores=False):
        """

        :param text:
        :param all_scores:
        :return:
        """

        sentiment = TextBlob(text, analyzer=self.nb).sentiment
        if all_scores:
            return dict(classification=sentiment.classification,
                        p_pos=round(sentiment.p_pos, 3),
                        p_neg=round(sentiment.p_neg, 3))
        return dict(classification=sentiment.classification)


class VaderAnalyzer:
    """

    """

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def evaluate(self, text, all_scores=True):
        """

        :param text:
        :param all_scores:
        :return:
        """
        score = self.analyzer.polarity_scores(text)
        if all_scores:
            return score
        return dict(compound=score.get('compound'))
