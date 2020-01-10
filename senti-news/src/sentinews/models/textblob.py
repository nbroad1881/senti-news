from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer


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
