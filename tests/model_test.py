import os
import pathlib

from dotenv import load_dotenv

from sentinews.models import TextBlobAnalyzer
from sentinews.models import VaderAnalyzer
from sentinews.models import LSTMAnalyzer

load_dotenv()


"""
Test if the models work as they should
"""

sentences = {
    'positive': "I'm having a wonderful day!",
    'negative': "This was a monumental waste of my time!",
    'neutral': "I am walking down the street.",
}

va = VaderAnalyzer()
tb = TextBlobAnalyzer()
lstm = LSTMAnalyzer(model_dir=os.environ.get('LSTM_PKL_MODEL_DIR'), model_name=os.environ.get('LSTM_PKL_FILENAME'))


for key, value in sentences.items():
    print(f"Sample {key} sentence: {value}")

for key, value in sentences.items():
    vader_score = va.evaluate(value, all_scores=True)
    textblob_score = tb.evaluate(value, all_scores=True, naive=True)
    lstm_score = lstm.evaluate(value)
    print('*' * 50)
    print(f"For {key} sentence:")
    print(f"Vader positive/negative/neutral/compound: "
          f"{vader_score['pos']}/{vader_score['neg']}/{vader_score['neu']}/{vader_score['compound']}")
    print(f"Textblob positive/negative: "
          f"{textblob_score['p_pos']}/{textblob_score['p_neg']}")
    print(f"LSTM positive/negative/neutral: "
          f"{lstm_score['p_pos']}/{lstm_score['p_neg']}/{lstm_score['p_neu']}")
