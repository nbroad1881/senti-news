from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer


class TextBlobAnalyzer:

    def __init__(self):
        pass

    def evaluate(self, texts, inc_subj=False, naive=False):
        """
        Return list of sentiments in same order as texts
        :param naive: Set to true to use the NaiveBayesAnalyzer, an NLTK classifier trained on movie reviews
        :param texts: list of strings
        :return: list of sentiment scores. Each score is a named tuple for polarity and subjectivity
        """
        if naive:
            return [self.nb_analyzer(text, inc_subj=inc_subj) for text in texts]

        sentiments = [TextBlob(text).sentiment for text in texts]
        if inc_subj:
            return [(senti.polarity, senti.subjectivity) for senti in sentiments]
        return [sentiment.polarity for sentiment in sentiments]

    @staticmethod
    def nb_analyzer(text, inc_subj=False):
        sentiment = TextBlob(text, analyzer=NaiveBayesAnalyzer).sentiment
        if inc_subj:
            return sentiment.polarity, sentiment.subjectivity
        return sentiment.polarity
