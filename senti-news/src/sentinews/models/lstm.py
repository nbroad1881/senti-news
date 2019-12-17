"""
This example shows how to use an LSTM sentiment classification model trained
using Keras in spaCy. spaCy splits the document into sentences, and each
sentence is classified using the LSTM. The scores for the sentences are then
aggregated to give the document score. This kind of hierarchical model is quite
difficult in "pure" Keras or Tensorflow, but it's very effective. The Keras
example on this dataset performs quite poorly, because it cuts off the documents
so that they're a fixed size. This hurts review accuracy a lot, because people
often summarise their rating in the final sentence
Prerequisites:
spacy download en_vectors_web_lg
pip install keras==2.0.9
Compatible with: spaCy v2.0.0+
"""
import os
import pathlib

import cytoolz
import numpy
from tensorflow.keras.models import model_from_json, save_model
import tensorflow as tf
from spacy.compat import pickle
import spacy
from fastai.text import load_learner
import numpy as np


class SentimentAnalyser(object):

    @classmethod
    def load(cls, path, nlp, max_length=100):
        with (path / "config_no_dropout.json").open() as file_:
            model = model_from_json(file_.read())
        with (path / "model").open("rb") as file_:
            lstm_weights = pickle.load(file_)
        embeddings = cls.get_embeddings(nlp.vocab)
        model.set_weights([embeddings] + lstm_weights)

        save_model(model, 'small3', save_format='tf')
        return cls(model, max_length=max_length)

    def __init__(self, model, max_length=100):
        self._model = model
        self.max_length = max_length

    def __call__(self, doc):
        X = self.get_features([doc], self.max_length)
        y = self._model.predict(X)
        self.set_sentiment(doc, y)

    @staticmethod
    def get_embeddings(vocab):
        return vocab.vectors.data

    def get_features(self, docs, max_length):
        docs = list(docs)
        Xs = numpy.zeros((len(docs), max_length), dtype="int32")
        for i, doc in enumerate(docs):
            j = 0
            for token in doc:
                vector_id = token.vocab.vectors.find(key=token.orth)
                if vector_id >= 0:
                    Xs[i, j] = vector_id
                else:
                    Xs[i, j] = 0
                j += 1
                if j >= max_length:
                    break
        return Xs

    def pipe(self, docs, batch_size=1000):
        for minibatch in cytoolz.partition_all(batch_size, docs):
            minibatch = list(minibatch)
            sentences = []
            for doc in minibatch:
                sentences.extend(doc.sents)
            Xs = self.get_features(sentences, self.max_length)
            ys = self._model.predict(Xs)
            for sent, label in zip(sentences, ys):
                sent.doc.sentiment += label - 0.5
            for doc in minibatch:
                yield doc

    def set_sentiment(self, doc, y):
        doc.sentiment = float(y[0])
        # Sentiment has a native slot for a single float.
        # For arbitrary data storage, there's:
        # doc.user_data['my_data'] = y


class LSTMAnalyzer:

    def __init__(self, model_dir='lstm_models', max_length=100):
        self.model_dir = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / pathlib.Path(model_dir)
        self.nlp = spacy.load("en_vectors_web_lg")
        self.nlp.add_pipe(self.nlp.create_pipe('sentencizer'))
        self.nlp.add_pipe(SentimentAnalyser.load(self.model_dir, self.nlp, max_length=max_length))

    # todo: have it setup before calling evaluate
    def evaluate(self, texts):
        return [doc.sentiment for doc in self.nlp.pipe(texts, batch_size=1000)]


class LSTMAnalyzer2:

    def __init__(self, model_name='lstm2.pkl'):
        self.model = load_learner(os.path.join(os.path.dirname(__file__), 'lstm_models/'), model_name)

    def evaluate(self, text):
        category, num_tensor, prob_tensor = self.model.predict(text)

        return {
            'category': str(category),
            'num': int(num_tensor),
            'p_pos': float(prob_tensor[2]),
            'p_neu': float(prob_tensor[1]),
            'p_neg': float(prob_tensor[0])
        }
