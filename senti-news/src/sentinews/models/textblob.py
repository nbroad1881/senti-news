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
            return TextBlobAnalyzer.nb_evaluate(texts, all_info=all_info)

        sentiments = [TextBlob(text).sentiment for text in texts]
        if all_info:
            return [dict(polarity=senti.polarity, subjectivity=senti.subjectivity) for senti in sentiments]
        return [dict(polarity=sentiment.polarity) for sentiment in sentiments]

    @staticmethod
    def nb_evaluate(texts, all_info=False):
        nb = NaiveBayesAnalyzer()
        sentiments = [TextBlob(text, analyzer=nb).sentiment for text in texts]
        if all_info:
            return [dict(classification=s.classification, p_pos=s.p_pos, p_neg=s.p_neg) for s in sentiments]
        return [dict(classification=s.classification) for s in sentiments]
