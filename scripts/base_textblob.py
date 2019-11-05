from textblob import TextBlob
import csv
import numpy as np


def analyze_text(in_filepath, out_filepath):
    with open(out_filepath, 'w') as s:
        s.write(
            'Made with base sentiment function in Textblob. Contains polarity and subjectivity of text. Polarity goes'
            'from [-1,1] and subjectivity goes from [0,1]\n')
        with open(in_filepath, 'r') as f:
            reader = csv.reader(f)
            counter = 1
            for row in reader:
                sent = TextBlob(row[4]).sentiment
                s.write(f"On {row[0][:10]}, the article '{row[1]}' has a sentiment score of {str(sent)}\n")
                print(f'{counter} done', end="\r")
                counter += 1


def aggregate_scores(filepath):
    pos = []
    sub = []
    with open(filepath, 'r') as f:
        headers = f.readline()
        for line in f:
            score = line[line.index('ity=') + 4:-1]
            positivity = float(score[:score.index(',')])
            subjectivity = float(score[score.index('ctivity=') + 8:-1])
            pos.append(positivity)
            sub.append(subjectivity)

    sub = np.array(sub)
    pos = np.array(pos)
    print(type(pos), pos[:10])
    num_neg = sum(pos <= -0.1)
    num_neu = sum(np.bitwise_and(sub > -0.1, sub < 0.1))
    num_pos = sum(sub >= 0.1)
    num_sub = sum(sub >= 0.5)

    print(f'Out of {len(pos)} articles:')
    print(f'Number of positive articles: {num_pos}')
    print(f'Number of neutral articles: {num_neu}')
    print(f'Number of negative articles: {num_neg}')
    print(f'Number of subjective articles: {num_sub}')


if __name__ == '__main__':
    choice = input('1. Analyze\n2. Aggregate\n')
    if choice == '1':
        analyze_text('../saved_texts/cnn_articles.csv', 'cnn_sentiment_scores_base_textblob.txt')
    elif choice == '2':
        aggregate_scores('sentiment_scores/cnn_sentiment_scores_base_textblob.txt')
