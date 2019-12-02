from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class VaderAnalyzer:

    def __init__(self):
        pass

    @staticmethod
    def evaluate(texts, all_scores=False):
        """
        Return list of sentiments in same order as texts
        :param texts: list of texts
        :return: list of scores. scores are dict with keys of
        neg, neu, pos, compound
        """
        analyzer = SentimentIntensityAnalyzer()
        scores = [analyzer.polarity_scores(text) for text in texts]
        if all_scores:
            return scores
        return [dict(compound=score.get('compound')) for score in scores]