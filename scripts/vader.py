import csv
import datetime
import logging

import spacy
import pathlib
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

CNN_DIR_PATH = pathlib.Path('../saved_texts/CNN/text_info/')
CNN_INFO_FILENAME = 'CNN_INFO.csv'
CNN_TITLE_COLUMN = 3

FOX_DIR_PATH = pathlib.Path('../saved_texts/FOX/text_info/')
FOX_INFO_FILENAME = 'FOX_INFO.csv'
FOX_TITLE_COLUMN = 2

NYT_DIR_PATH = pathlib.Path('../saved_texts/NYT/text_info/')
NYT_INFO_FILENAME = 'NYT_INFO.csv'
NYT_TITLE_COLUMN = 3

logging.basicConfig(level=logging.INFO)
nlp = spacy.load("en_core_web_sm")
"""
Vader is trained on social media posts and is relatively straightforward
to implement. It will be one of the first approaches for sentiment analysis
of news articles. 
Scores are as follows:
positive sentiment = compound score >= 0.05
neutral sentiment = (compound score > -0.05) and (compound score < 0.05)
negative sentiment = compound score <= -0.05
"""


def score_texts(texts):
    """
    Return list of sentiments in same order as texts
    :param texts: list of texts
    :return: list of scores. scores are dict with keys of
    neg, neu, pos, compound
    """
    analyzer = SentimentIntensityAnalyzer()
    scores = [analyzer.polarity_scores(text) for text in texts]
    return scores


def load_texts(filepath, column):
    """
    The titles are stored in csv files, and the column for title
    is inconsistent. Assumes there are no headers in csv
    :param filepath: path to csv
    :param column: column in csv that corresponds to titles
    :return: list of titles
    """
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        return [row[column] for row in reader]

def clean_texts(texts):
    """
    Vader will automatically do this.
    :param texts:
    :return:
    """
    clean_text = []
    for text in texts:
        doc = nlp(text)
        sentence = ' '.join([token.lemma_ for token in doc if not token.is_stop])
        clean_text.append(sentence)
    return clean_text

def get_score_counts(scores):
    """
    Print the number of positive, neutral, and negative scores
    for a given list of scores
    :param scores: list of vader scores
    :return: None
    """

def aggregate_scores(filepath):
    neg = []
    neu = []
    pos = []
    com = []
    with open(filepath, 'r') as f:
        headers = f.readline()
        for line in f:
            score = line[line.index('{'):-1]
            j = json.loads(score.replace("'", '"'))
            neg.append(j['neg'])
            neu.append(j['neu'])
            pos.append(j['pos'])
            com.append(j['compound'])

    neg = np.array(neg)
    neu = np.array(neu)
    pos = np.array(pos)
    com = np.array(com)
    num_neg = sum(com <= -0.05)
    num_neu = sum(np.bitwise_and(com > -0.05, com < 0.05))
    num_pos = sum(com >= 0.05)

    print(f'Out of {len(neg)} articles:')
    print(f'Number of positive articles: {num_pos}')
    print(f'Number of neutral articles: {num_neu}')
    print(f'Number of negative articles: {num_neg}')


if __name__ == '__main__':
    choice = input("Which news company to analyze?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n")
    if choice == '1':
        texts = load_texts((CNN_DIR_PATH / CNN_INFO_FILENAME), CNN_TITLE_COLUMN)
    elif choice == '2':
        texts = load_texts((FOX_DIR_PATH / FOX_INFO_FILENAME), FOX_TITLE_COLUMN)
    elif choice == '3':
        texts = load_texts((NYT_DIR_PATH / NYT_INFO_FILENAME), NYT_TITLE_COLUMN)
    scores = score_texts(texts)
    get_score_counts(scores)
    print(list(zip(texts, scores)))