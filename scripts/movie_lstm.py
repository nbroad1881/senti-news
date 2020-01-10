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
import csv

import plac
import random
import pathlib
import cytoolz
import numpy
from keras.models import Sequential, model_from_json
from keras.layers import LSTM, Dense, Embedding, Bidirectional
from keras.layers import TimeDistributed
from keras.optimizers import Adam
import thinc.extra.datasets
from spacy.compat import pickle
import spacy

TEXTS_DIR = '/Users/nicholasbroad/PycharmProjects/senti-news/saved_texts/FOX/texts'
SENTIMENT_SCORE_CSV = 'LSTM_FOX_TITLE_SCORES.CSV'

CNN_DIR_PATH = pathlib.Path('../saved_texts/CNN/text_info/')
CNN_INFO_FILENAME = 'CNN_INFO.csv'
CNN_TITLE_COLUMN = 3

FOX_DIR_PATH = pathlib.Path('../saved_texts/FOX/text_info/')
FOX_INFO_FILENAME = 'FOX_INFO.csv'
FOX_TITLE_COLUMN = 2

NYT_DIR_PATH = pathlib.Path('../saved_texts/NYT/text_info/')
NYT_INFO_FILENAME = 'NYT_INFO.csv'
NYT_TITLE_COLUMN = 3


class SentimentAnalyser(object):
    @classmethod
    def load(cls, path, nlp, max_length=100):
        with (path / "config.json").open() as file_:
            model = model_from_json(file_.read())
        with (path / "model").open("rb") as file_:
            lstm_weights = pickle.load(file_)
        embeddings = get_embeddings(nlp.vocab)
        model.set_weights([embeddings] + lstm_weights)
        return cls(model, max_length=max_length)

    def __init__(self, model, max_length=100):
        self._model = model
        self.max_length = max_length

    def __call__(self, doc):
        X = get_features([doc], self.max_length)
        y = self._model.predict(X)
        self.set_sentiment(doc, y)

    def pipe(self, docs, batch_size=1000):
        for minibatch in cytoolz.partition_all(batch_size, docs):
            minibatch = list(minibatch)
            sentences = []
            for doc in minibatch:
                sentences.extend(doc.sents)
            Xs = get_features(sentences, self.max_length)
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


def get_labelled_sentences(docs, doc_labels):
    labels = []
    sentences = []
    for doc, y in zip(docs, doc_labels):
        for sent in doc.sents:
            sentences.append(sent)
            labels.append(y)
    return sentences, numpy.asarray(labels, dtype="int32")


def get_features(docs, max_length):
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


def train(
        train_texts,
        train_labels,
        dev_texts,
        dev_labels,
        lstm_shape,
        lstm_settings,
        lstm_optimizer,
        batch_size=100,
        nb_epoch=5,
        by_sentence=True,
):
    print("Loading spaCy")
    nlp = spacy.load("en_vectors_web_lg")
    nlp.add_pipe(nlp.create_pipe("sentencizer"))
    embeddings = get_embeddings(nlp.vocab)
    model = compile_lstm(embeddings, lstm_shape, lstm_settings)

    print("Parsing texts...")
    train_docs = list(nlp.pipe(train_texts))
    dev_docs = list(nlp.pipe(dev_texts))
    if by_sentence:
        train_docs, train_labels = get_labelled_sentences(train_docs, train_labels)
        dev_docs, dev_labels = get_labelled_sentences(dev_docs, dev_labels)

    train_X = get_features(train_docs, lstm_shape["max_length"])
    dev_X = get_features(dev_docs, lstm_shape["max_length"])
    model.fit(
        train_X,
        train_labels,
        validation_data=(dev_X, dev_labels),
        epochs=nb_epoch,
        batch_size=batch_size,
    )
    return model


def compile_lstm(embeddings, shape, settings):
    model = Sequential()
    model.add(
        Embedding(
            embeddings.shape[0],
            embeddings.shape[1],
            input_length=shape["max_length"],
            trainable=False,
            weights=[embeddings],
            mask_zero=True,
        )
    )
    model.add(TimeDistributed(Dense(shape["nr_hidden"], use_bias=False)))
    model.add(
        Bidirectional(
            LSTM(
                shape["nr_hidden"],
                recurrent_dropout=settings["dropout"],
                dropout=settings["dropout"],
            )
        )
    )
    model.add(Dense(shape["nr_class"], activation="sigmoid"))
    model.compile(
        optimizer=Adam(lr=settings["lr"]),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def get_embeddings(vocab):
    return vocab.vectors.data


# todo: standardize the columns in csvs
def evaluate(model_dir, text_dir, max_length=100, is_csv=False, title_col_num=3, id_col_num=2):
    nlp = spacy.load("en_vectors_web_lg")
    nlp.add_pipe(nlp.create_pipe("sentencizer"))
    nlp.add_pipe(SentimentAnalyser.load(model_dir, nlp, max_length=max_length))

    texts = []
    ids = []
    if is_csv:
        with open(text_dir, 'r') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                texts.append(row[title_col_num])
                ids.append(row[id_col_num])
    else:
        for entry in os.scandir(text_dir):
            if entry.is_file() and os.path.splitext(entry)[1] == '.txt':
                with open(entry, 'r') as file:
                    texts.append(file.read())
                ids.append(os.path.split(entry)[1])
    sentiments = []
    for doc in nlp.pipe(texts, batch_size=1000):
        sentiments.append(doc.sentiment)
    with open(text_dir, 'r') as file:
        old_rows = [row for row in csv.reader(file)]
    with open(text_dir, 'w') as file:
        writer = csv.writer(file)
        for index, old_row in enumerate(old_rows):
            new_col = f'LSTM({round(sentiments[index],3)})'
            writer.writerow(old_row+[new_col])


def read_data(data_dir, limit=0):
    examples = []
    for subdir, label in (("pos", 1), ("neg", 0)):
        for filename in (data_dir / subdir).iterdir():
            with filename.open() as file_:
                text = file_.read()
            examples.append((text, label))
    random.shuffle(examples)
    if limit >= 1:
        examples = examples[:limit]
    return zip(*examples)  # Unzips into two lists


@plac.annotations(
    train_dir=("Location of training file or directory"),
    dev_dir=("Location of development file or directory"),
    model_dir=("Location of output model directory",),
    is_runtime=("Demonstrate run-time usage", "flag", "r", bool),
    nr_hidden=("Number of hidden units", "option", "H", int),
    max_length=("Maximum sentence length", "option", "L", int),
    dropout=("Dropout", "option", "d", float),
    learn_rate=("Learn rate", "option", "e", float),
    nb_epoch=("Number of training epochs", "option", "i", int),
    batch_size=("Size of minibatches for training LSTM", "option", "b", int),
    nr_examples=("Limit to N examples", "option", "n", int),
)
def main(
        model_dir=None,
        train_dir=None,
        dev_dir=None,
        is_runtime=False,
        nr_hidden=64,
        max_length=100,  # Shape
        dropout=0.5,
        learn_rate=0.001,  # General NN config
        nb_epoch=5,
        batch_size=256,
        nr_examples=-1,
):  # Training params
    if model_dir is not None:
        model_dir = pathlib.Path(model_dir)
    if train_dir is None or dev_dir is None:
        imdb_data = thinc.extra.datasets.imdb()
    if is_runtime:
        evaluate(model_dir, (FOX_DIR_PATH / FOX_INFO_FILENAME), max_length=max_length, is_csv=True, title_col_num=FOX_TITLE_COLUMN, id_col_num=1)
    else:
        if train_dir is None:
            train_texts, train_labels = zip(*imdb_data[0])
        else:
            print("Read data")
            train_texts, train_labels = read_data(train_dir, limit=nr_examples)
        if dev_dir is None:
            dev_texts, dev_labels = zip(*imdb_data[1])
        else:
            dev_texts, dev_labels = read_data(dev_dir, imdb_data, limit=nr_examples)
        train_labels = numpy.asarray(train_labels, dtype="int32")
        dev_labels = numpy.asarray(dev_labels, dtype="int32")
        lstm = train(
            train_texts,
            train_labels,
            dev_texts,
            dev_labels,
            {"nr_hidden": nr_hidden, "max_length": max_length, "nr_class": 1},
            {"dropout": dropout, "lr": learn_rate},
            {},
            nb_epoch=nb_epoch,
            batch_size=batch_size,
        )
        weights = lstm.get_weights()
        if model_dir is not None:
            with (model_dir / "model").open("wb") as file_:
                pickle.dump(weights[1:], file_)
            with (model_dir / "config.json").open("w") as file_:
                file_.write(lstm.to_json())
        else:
            with open("model", "wb") as file_:
                pickle.dump(weights[1:], file_)
            with open("config.json", "w") as file_:
                file_.write(lstm.to_json())


if __name__ == "__main__":
    plac.call(main)
