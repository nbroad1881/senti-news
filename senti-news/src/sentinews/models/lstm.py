import os
import pathlib

from fastai.text import load_learner

"""
The model is trained using the ULMFit technique of transfer learning for NLP purposes.
The starting model is already a language model trained on wikipedia.
The language model then gets trained with 1000 articles.
Then the model becomes a classifier and gets trained on  few hundred hand-labeled news titles.
The saved model is then stored locally.
"""

class LSTMAnalyzer:

    def __init__(self, model_dir='src/sentinews/models/lstm_models', model_name='lstm2.pkl'):
        self.model_dir = pathlib.Path('/Users/nicholasbroad/PycharmProjects/senti-news/senti-news/src/sentinews/models/lstm_models')
        self.model = load_learner(self.model_dir, model_name)

    def evaluate(self, text):
        category, num_tensor, prob_tensor = self.model.predict(text)

        return {
            'category': str(category),
            'num': int(num_tensor),
            'p_pos': float(prob_tensor[2]),
            'p_neu': float(prob_tensor[1]),
            'p_neg': float(prob_tensor[0])
        }
