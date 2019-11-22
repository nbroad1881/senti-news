from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer


class TextBlobAnalyzer:
    """

    """

    @staticmethod
    def evaluate(texts, all_info=False, naive=False):
        """
        Return list of sentiments in same order as texts
        :param naive: Set to true to use the NaiveBayesAnalyzer, an NLTK classifier trained on movie reviews
        :param texts: list of strings
        :return: list of sentiment scores. Each score is a named tuple for polarity and subjectivity
        """
        if naive:
            return [TextBlobAnalyzer.nb_analyzer(text, all_info=all_info) for text in texts]

        sentiments = [TextBlob(text).sentiment for text in texts]
        if all_info:
            return [(senti.polarity, senti.subjectivity) for senti in sentiments]
        return [sentiment.polarity for sentiment in sentiments]

    @staticmethod
    def nb_analyzer(text, all_info=False):
        sentiment = TextBlob(text, analyzer=NaiveBayesAnalyzer()).sentiment
        if all_info:
            return sentiment.classification, sentiment.p_pos, sentiment.p_neg
        return sentiment.classification
