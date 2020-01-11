import csv
import datetime
import pathlib
import logging

import numpy as np

POSITIVE_LIST_PATH = '../saved_texts/opinion-lexicon-English/positive-words.txt'
NEGATIVE_LIST_PATH = '../saved_texts/opinion-lexicon-English/negative-words.txt'

NUM_POSITIVE_LINES_TO_SKIP = 30
NUM_NEGATIVE_LINES_TO_SKIP = 31

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


def load_positive_set(filepath):
    """
    Loads each word in the text file to a set.
    Ignores UnicodeDecodeErrors
    :param filepath:
    :return:
    """
    with open(filepath, 'r', errors='ignore') as file:
        for _ in range(NUM_POSITIVE_LINES_TO_SKIP):
            file.readline()
        words = set()
        for word in file:
            words.add(word.strip())

    return words


def load_negative_set(filepath):
    """
    Loads each word in the text file to a set.
    Ignores UnicodeDecodeErrors
    :param filepath:
    :return:
    """
    with open(filepath, 'r', errors='ignore') as file:
        for _ in range(NUM_NEGATIVE_LINES_TO_SKIP):
            file.readline()
        words = set()

        for word in file:
            words.add(word.strip())

    return words


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


def score_texts(texts, positive_set, negative_set):
    """
    Return list of sentiments in same order as texts
    :param negative_set:
    :param positive_set:
    :param clean:
    :param texts: list of strings
    :return: list of sentiment scores. Each score is a named tuple for polarity and subjectivity
    """
    scores = []
    for text in texts:
        pos_score = 0
        neg_score = 0
        logging.debug(f'Current text = {text}')
        for word in text.split(' '):
            if word.lower() in positive_set:
                logging.debug('Found positive word')
                pos_score += 1
            if word.lower() in negative_set:
                logging.debug('Found negative word')
                neg_score += 1
        scores.append((pos_score, neg_score))
    return scores


def print_score_counts(scores):
    """
    Print the number of positive, neutral, and negative scores
    for a given list of scores
    :param scores: list of TextBlob sentiments
    :return: None
    """

    pos_scores = np.array([score[0] for score in scores])
    neg_scores = np.array([score[1] for score in scores])
    compound = pos_scores - neg_scores

    print(f'Out of {len(compound)} texts:\n'
          f'Number of positive articles: {sum(compound > 0)}\n'
          f'Number of neutral articles: {sum(compound == 0)}\n'
          f'Number of negative articles: {sum(compound < 0)}\n')


def to_integer_labels(scores):
    """
    Return a list of integers where -1 corresponds to negative label,
    0 corresponds to neutral, and +1 corresponds to positive label.
    :param scores: list of Sentiments
    :return: list of integers
    """
    integer_labels = []
    for score in scores:
        compound = score[0] - score[1]  # positive - negative
        if compound > 0:
            integer_labels.append(1)
        elif compound == 0:
            integer_labels.append(0)
        elif compound < 0:
            integer_labels.append(-1)
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
            new_col = f'Lexicon({today}):' \
                      f'Positive={scores[index][0]}' \
                      f'Negative={scores[index][1]}'
            writer.writerow(old_row + [new_col])


def main():
    choice = input("Which news company to analyze?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n")
    if choice == '1':
        csv_file_path = (CNN_DIR_PATH / CNN_INFO_FILENAME)
        col_num = CNN_TITLE_COLUMN
    elif choice == '2':
        csv_file_path = (FOX_DIR_PATH / FOX_INFO_FILENAME)
        col_num = FOX_TITLE_COLUMN
    elif choice == '3':
        csv_file_path = (NYT_DIR_PATH / NYT_INFO_FILENAME)
        col_num = NYT_TITLE_COLUMN
    else:
        return
    pos_set = load_positive_set(POSITIVE_LIST_PATH)
    neg_set = load_negative_set(NEGATIVE_LIST_PATH)
    texts = load_texts(csv_file_path, col_num)
    scores = score_texts(texts, pos_set, neg_set)
    print_score_counts(scores)
    scores_to_csv(csv_file_path, scores)

if __name__ == '__main__':
    main()
