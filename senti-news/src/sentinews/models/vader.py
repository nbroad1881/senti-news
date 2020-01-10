from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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