from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from sklearn.linear_model import LinearRegression
from spacy.lang.en.stop_words import STOP_WORDS
import spacy
from spacy.tokenizer import Tokenizer
import csv
import pickle
import sys


def load_text_from_file(filepath, isText=True):
    """If **isText is False, treats the file as csv, parses each line."""
    try:
        with open(filepath, 'r') as f:
            if isText:
                text = f.read()
                return text
            else:
                try:
                    reader = csv.reader(f)
                    lines = []
                    for line in reader:
                        if len(line[0]) > 5:
                            lines.append(line[0])
                    return lines
                except Exception:
                    print('Invalid file extension:', ext)
                    return ''
    except IOError:
        print('Could not open file', filepath)
        return ''

    return txt.strip()


if __name__ == '__main__':

    dump = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'p':
            """p flag to use pickeled data"""
            with open('../texts/pickled_matrices', 'rb') as f:
                [whole_doc, X_train, X_test, y_train, y_test] = pickle.load(f)
        elif sys.argv[1] == 'd':
            """d flag to dump pickled data"""
            dump = True
    else:

        nlp = spacy.load('en_core_web_sm')

        train_text = []
        for n in range(14, 26, 1):
            train_text.append(load_text_from_file(f'/texts/text-2019-09-{n}.csv',
                                                  True))

        docs = list(nlp.tokenizer.pipe(train_text, batch_size=2))

        cv = CountVectorizer(max_features=10000, stop_words=STOP_WORDS)
        whole_doc = cv.fit_transform(docs)

        nms = cv.get_feature_names()[:10]
        print(nms)
        print(whole_doc.toarray()[0, :10])

        temp = list(zip(cv.get_feature_names(),
                        np.sum(whole_doc.toarray(), axis=0)))
        pairs = np.array(temp, dtype=[('word', '<U21'), ('sum', 'i4')])
        ordered = np.flip(np.sort(pairs, order='sum'))
        print(ordered[:10])  # highest 10 counts

        X_train = cv.transform(docs[:-1])
        X_test = cv.transform([docs[-1]])

        with open('/texts/poll_ratings_9-13-to-10-1.csv', 'r') as polls:
            reader = csv.reader(polls)
            next(reader)  # skipping headers
            ratings = []
            for row in reader:
                ratings.append(row)

        ratings = np.array(ratings[:12])[:, 1:].astype(np.float)
        y_train = ratings[:-1]
        y_test = ratings[-1]

        if dump:
            with open('../texts/pickled_matrices', 'wb') as f:
                pickle.dump([whole_doc, X_train, X_test, y_train, y_test], f)

    model = LinearRegression()
    model.fit(X_train, y_train)

    prediction = model.predict(X_test)

    print('LR Predictions:', np.around(prediction, decimals=2)[0])
    print('Actual:', y_test)
