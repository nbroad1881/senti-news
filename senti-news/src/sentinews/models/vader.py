from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class VaderAnalyzer:

    def __init__(self):
        pass

    @staticmethod
    def evaluate(text, all_scores=False):
        """
        Return list of sentiments in same order as texts
        :param texts: list of texts
        :return: list of scores. scores are dict with keys of
        neg, neu, pos, compound
        """

        score = self.analyzer.polarity_scores(text)
        if all_scores:
            return score
        return dict(compound=score.get('compound'))