import csv
from datetime import datetime
import logging

from dateutil.parser import isoparse
import spacy
import pathlib
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Text, Float



"""
This is the old vader model file. Will likely delete soon.
"""

CNN_DIR_PATH = pathlib.Path('../saved_texts/CNN/text_info/')
CNN_INFO_FILENAME = 'CNN_INFO.csv'
CNN_TITLE_COLUMN = 3

FOX_DIR_PATH = pathlib.Path('../saved_texts/FOX/text_info/')
FOX_INFO_FILENAME = 'FOX_INFO.csv'
FOX_TITLE_COLUMN = 2

NYT_DIR_PATH = pathlib.Path('../saved_texts/NYT/text_info/')
NYT_INFO_FILENAME = 'NYT_INFO.csv'
NYT_TITLE_COLUMN = 3

DB_URL = "postgresql://nicholasbroad:@localhost:5432/nicholasbroad"

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


def score_texts(text):
    """
    Return list of sentiments in same order as texts
    :param texts: list of texts
    :return: list of scores. scores are dict with keys of
    neg, neu, pos, compound
    """
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)


def load_texts(filepath, column, all_columns=None):
    """
    The titles are stored in csv files, and the column for title
    is inconsistent. Assumes there are no headers in csv
    :param all_columns: set True to return all columns in row rather than just specified column
    :param filepath: path to csv
    :param column: column in csv that corresponds to titles
    :return: list of titles
    """
    with open(filepath, 'r') as file:
        reader = csv.reader(file)
        if all_columns:
            return [row for row in reader]
        else:
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


def print_score_counts(scores):
    """
    Print the number of positive, neutral, and negative scores
    for a given list of scores
    :param scores: list of vader scores
    :return: None
    """

    compound = np.array([score['compound'] for score in scores])
    num_negative_scores = sum(compound <= -0.05)
    num_neutral_scores = sum(np.bitwise_and(compound > -0.05, compound < 0.05))
    num_positive_scores = sum(compound >= 0.05)

    print(f'Out of {len(compound)} texts:\n'
          f'Number of positive articles: {num_positive_scores}\n'
          f'Number of neutral articles: {num_neutral_scores}\n'
          f'Number of negative articles: {num_negative_scores}')


def to_integer_labels(scores):
    """
    Return a list of integers where -1 corresponds to negative label,
    0 corresponds to neutral, and +1 corresponds to positive label.
    :param scores: list of Sentiments
    :return: list of integers
    """
    integer_labels = []
    for score in scores:
        if score['compound'] <= -0.05:
            integer_labels.append(-1)
        elif score['compound'] > -0.05 and score['compound'] < 0.05:
            integer_labels.append(0)
        elif score['compound'] > 0.05:
            integer_labels.append(1)
        else:  # this should hopefully never happen
            integer_labels.append(None)
    return integer_labels


def scores_to_csv(filepath, scores):
    """
    Adds a column of compound scores labelled with the date
    to the csv.
    :param filepath: path to csv
    :param scores: list of scores
    :return: None
    """

    with open(filepath, 'r') as file:
        old_rows = [row for row in csv.reader(file)]
    with open(filepath, 'w') as file:
        writer = csv.writer(file)
        for index, old_row in enumerate(old_rows):
            date = datetime.date.today().isoformat()
            new_col = f'VADER({date}):{scores[index]["compound"]}'
            writer.writerow(old_row + [new_col])


def record_to_db(rows, scores, table, conn):
    """
    :param table:
    :param rows: List of information from csv like url, title, date
    :param scores: Vader sentiment scores
    :param conn: engine connection
    :return: None
    """
    for i, row in enumerate(rows):
        ins = table.insert().values(
            {
                'url': row[0],
                'date': isoparse(row[1]),
                'title': row[3],
                'publisher': 'CNN',
                'content': '',
                'vader_positive': scores[i].get('pos'),
                'vader_neutral': scores[i].get('neu'),
                'vader_negative': scores[i].get('neg'),
                'vader_compound': scores[i].get('compound')
            }
        )
        conn.execute(ins)


def clean_text(text):
    import re
    pattern = re.compile('[^a-zA-Z\d\s:]+', re.UNICODE)
    return pattern.sub('', text)


def make_vader_table(engine):
    meta = MetaData()
    vader_scores = Table('vader_scores', meta,
                         Column('url', String(200), primary_key=True),
                         Column('date', DateTime(), default=datetime.utcnow()),
                         Column('title', Text),
                         Column('publisher', String(20)),
                         Column('content', Text),
                         Column('vader_positive', Float),
                         Column('vader_neutral', Float),
                         Column('vader_negative', Float),
                         Column('vader_compound', Float))
    vader_scores.create(engine)
    return vader_scores


def main():
    choice = input("Which news company to analyze?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n")
    if choice == '1':
        csv_path = (CNN_DIR_PATH / CNN_INFO_FILENAME)
        col_num = CNN_TITLE_COLUMN
    elif choice == '2':
        csv_path = (FOX_DIR_PATH / FOX_INFO_FILENAME)
        col_num = FOX_TITLE_COLUMN
    elif choice == '3':
        csv_path = (NYT_DIR_PATH / NYT_INFO_FILENAME)
        col_num = NYT_TITLE_COLUMN
    choice = input("Create vader table? (Y/N) ").lower()
    if choice == 'y':
        engine = create_engine(DB_URL)
        make_vader_table(engine)
    choice = input("Transfer scores to database? (Y/N) ").lower()
    if choice == 'y':
        rows = load_texts(filepath=csv_path, column=None, all_columns=True)
        texts = [row[col_num] for row in rows]
        scores = score_texts(texts)

        engine = create_engine(DB_URL)
        conn = engine.connect()
        meta = MetaData()
        table = Table('vader_scores', meta, autoload=True, autoload_with=engine)
        record_to_db(rows=rows, scores=scores, table=table, conn=conn)
        conn.close()
    else:
        texts = load_texts(csv_path, col_num)
        scores = score_texts(texts)
        print_score_counts(scores)
        scores_to_csv(csv_path, scores)


if __name__ == '__main__':
    main()
