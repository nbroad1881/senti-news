from sentinews.models.textblob import TextBlobAnalyzer
from sentinews.models.vader import VaderAnalyzer
from sentinews.models.lstm import LSTMAnalyzer


"""
Test if the models work as they should
"""



print(VaderAnalyzer.evaluate(["I'm having a terribly good day!"], all_scores=True))
print(TextBlobAnalyzer.evaluate(["I'm having a terribly good day!"], all_info=True, naive=False))
print(LSTMAnalyzer().evaluate('lstm_models', ["I'm having a terribly good day!"]))
