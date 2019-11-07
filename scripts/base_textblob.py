import datetime
import pathlib
import csv
import logging

import spacy
import numpy as np
from textblob import TextBlob

CNN_DIR_PATH = pathlib.Path('../saved_texts/CNN/text_info/')
CNN_INFO_FILENAME = 'CNN_INFO.csv'
CNN_TITLE_COLUMN = 3

FOX_DIR_PATH = pathlib.Path('../saved_texts/FOX/text_info/')
FOX_INFO_FILENAME = 'FOX_INFO.csv'
FOX_TITLE_COLUMN = 2

NYT_DIR_PATH = pathlib.Path('../saved_texts/NYT/text_info/')
NYT_INFO_FILENAME = 'NYT_INFO.csv'
NYT_TITLE_COLUMN = 3

POSITIVE_NEUTRAL_BOUNDARY = 0.33
NEGATIVE_NEUTRAL_BOUNDARY = -0.33
SUBJECTIVE_BOUNDARY = 0.5

logging.basicConfig(level=logging.INFO)
nlp = spacy.load("en_core_web_sm")
"""
Made with base sentiment function in TextBlob. Contains polarity and subjectivity of text. 
Polarity goes from [-1,1] and subjectivity goes from [0,1]
"""


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


def score_texts(texts, clean=False):
    """
    Return list of sentiments in same order as texts
    :param clean:
    :param texts: list of strings
    :return: list of sentiment scores. Each score is a named tuple for polarity and subjectivity
    """
    if clean:
        return [TextBlob(text).sentiment for text in clean_texts(texts)]
    return [TextBlob(text).sentiment for text in texts]


def clean_texts(texts):
    """
    Unsure if TextBlob automatically does this
    :param texts: list of strings
    :return: list of strings with stop words removed and lemmatized
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
    :param scores: list of TextBlob sentiments
    :return: None
    """

    polarities = np.array([score.polarity for score in scores])
    subjectivities = np.array([score.subjectivity for score in scores])
    num_negative_scores = sum(polarities <= NEGATIVE_NEUTRAL_BOUNDARY)
    num_neutral_scores = sum(np.bitwise_and(polarities > NEGATIVE_NEUTRAL_BOUNDARY,
                                            polarities < POSITIVE_NEUTRAL_BOUNDARY))
    num_positive_scores = sum(polarities >= POSITIVE_NEUTRAL_BOUNDARY)
    num_subjective_scores = sum(subjectivities >= SUBJECTIVE_BOUNDARY)
    num_objective_scores = sum(subjectivities < SUBJECTIVE_BOUNDARY)

    print(f'Out of {len(polarities)} texts:\n'
          f'Number of positive articles: {num_positive_scores}\n'
          f'Number of neutral articles: {num_neutral_scores}\n'
          f'Number of negative articles: {num_negative_scores}\n'
          f'Number of subjective articles: {num_subjective_scores}\n'
          f'Number of objective articles: {num_objective_scores}')


def to_integer_labels(scores):
    """
    Return a list of integers where -1 corresponds to negative label,
    0 corresponds to neutral, and +1 corresponds to positive label.
    :param scores: list of Sentiments
    :return: list of integers
    """
    integer_labels = []
    for score in scores:
        if score.polarity <= NEGATIVE_NEUTRAL_BOUNDARY:
            integer_labels.append(-1)
        elif NEGATIVE_NEUTRAL_BOUNDARY < score.polarity < POSITIVE_NEUTRAL_BOUNDARY:
            integer_labels.append(0)
        elif score.polarity > POSITIVE_NEUTRAL_BOUNDARY:
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
            today = datetime.date.today().isoformat()
            new_col = f'TextBlob({today}):' \
                      f'Polarity={round(scores[index].polarity, 3)}' \
                      f'Subjectivity={round(scores[index].polarity, 3)}'
            writer.writerow(old_row + [new_col])


def main():
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
    scores = score_texts(texts, clean=True)
    get_score_counts(scores)


if __name__ == '__main__':
    main()
