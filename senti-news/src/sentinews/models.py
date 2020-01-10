import pathlib

from fastai.text import load_learner
from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

"""
Combining all models into a single file because they aren't that complicated.
"""



"""
The model is trained using the ULMFit technique of transfer learning for NLP purposes.
The starting model is already a language model trained on wikipedia.
The language model then gets trained with 1000 articles.
Then the model becomes a classifier and gets trained on  few hundred hand-labeled news titles.
The saved model is then stored locally.
"""

class LSTMAnalyzer:

    # todo: figure out how to handle file better
    def __init__(self, model_dir='src/sentinews/models/lstm_pkls', model_name='lstm2.pkl'):
        self.model_dir = pathlib.Path('/Users/nicholasbroad/PycharmProjects/senti-news/senti-news/src/sentinews/lstm_pkls')
        self.model = load_learner(self.model_dir, model_name)

    def evaluate(self, text):
        category, num_tensor, prob_tensor = self.model.predict(text)

        return {
            'category': str(category),
            'num': int(num_tensor),
            'p_pos': float(prob_tensor[2]),
            'p_neu': float(prob_tensor[1]),
            'p_neg': float(prob_tensor[0])
        }


class TextBlobAnalyzer:
    """

    """

    def __init__(self):
        self.nb = NaiveBayesAnalyzer()


    def evaluate(self, text, all_scores=True, naive=True):
        """
        Return list of sentiments in same order as texts
        :param naive: Set to true to use the NaiveBayesAnalyzer, an NLTK classifier trained on movie reviews
        :param text: string sentence to be analyzed
        :return: list of sentiment scores. Each score is a named tuple for polarity and subjectivity
        """
        if naive:
            return self.nb_evaluate(text, all_scores=all_scores)

        sentiment = TextBlob(text).sentiment
        if all_scores:
            return dict(polarity=sentiment.polarity, subjectivity=sentiment.subjectivity)
        return dict(polarity=sentiment.polarity)

    def nb_evaluate(self, text, all_scores=False):

        sentiment = TextBlob(text, analyzer=self.nb).sentiment
        if all_scores:
            return dict(classification=sentiment.classification,
                        p_pos=sentiment.p_pos,
                        p_neg=sentiment.p_neg)
        return dict(classification=sentiment.classification)


class VaderAnalyzer:

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()


    def evaluate(self, text, all_scores=True):
        """
        Return list of sentiments in same order as texts
        :param text: sentence to be analyzed
        :return: list of scores. scores are dict with keys of
        neg, neu, pos, compound
        """

        score = self.analyzer.polarity_scores(text)
        if all_scores:
            return score
        return dict(compound=score.get('compound'))