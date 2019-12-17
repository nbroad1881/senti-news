from sentinews.models.textblob import TextBlobAnalyzer
from sentinews.models.vader import VaderAnalyzer
from sentinews.models.lstm import LSTMAnalyzer


"""
Test if the models work as they should
"""

positive_sentence = "I'm having a wonderful day!"
negative_sentence = "This was a monumental waste of my time!"
neutral_sentence = "I am walking down the street."
va = VaderAnalyzer()

vader_pos = va.evaluate([positive_sentence], all_scores=False)
vader_neg = va.evaluate([negative_sentence], all_scores=False)
vader_neu = va.evaluate([neutral_sentence], all_scores=False)

tb = TextBlobAnalyzer()

textblob_pos = tb.evaluate([positive_sentence], all_scores=True, naive=False)
textblob_neg = tb.evaluate([negative_sentence], all_scores=True, naive=False)
textblob_neu = tb.evaluate([neutral_sentence], all_scores=True, naive=False)

lstm = LSTMAnalyzer(model_dir='lstm_models')
lstm_pos = lstm.evaluate([positive_sentence])
lstm_neg = lstm.evaluate([negative_sentence])
lstm_neu = lstm.evaluate([neutral_sentence])

print(f"Sample positive sentence: {positive_sentence}")
print(f"Sample negative sentence: {negative_sentence}")
print(f"Sample neutral sentence: {neutral_sentence}")
print(f"Vader positive/negative/neutral: {vader_pos}/{vader_neg}/{vader_neu}")
print(f"Textblob positive/negative/neutral: {textblob_pos}/{textblob_neg}/{textblob_neu}")
print(f"LSTM positive/negative/neutral: {lstm_pos}/{lstm_neg}/{lstm_neu}")
