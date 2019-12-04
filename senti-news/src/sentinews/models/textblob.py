from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer


class TextBlobAnalyzer:
    """

    """
    nb = NaiveBayesAnalyzer()
    def evaluate(self, texts, all_scores=False, naive=False):
        """
        Return list of sentiments in same order as texts
        :param naive: Set to true to use the NaiveBayesAnalyzer, an NLTK classifier trained on movie reviews
        :param texts: list of strings
        :return: list of sentiment scores. Each score is a named tuple for polarity and subjectivity
        """
        if naive:
            return self.nb_evaluate(texts, all_scores=all_scores)

        sentiments = [TextBlob(text).sentiment for text in texts]
        if all_scores:
            return [dict(polarity=senti.polarity, subjectivity=senti.subjectivity) for senti in sentiments]
        return [dict(polarity=sentiment.polarity) for sentiment in sentiments]

    def nb_evaluate(self, texts, all_scores=False):

        sentiments = [TextBlob(text, analyzer=self.nb).sentiment for text in texts]
        if all_scores:
            return [dict(classification=s.classification, p_pos=s.p_pos, p_neg=s.p_neg) for s in sentiments]
        return [dict(classification=s.classification) for s in sentiments]
