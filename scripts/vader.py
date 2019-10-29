from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv
import json
import numpy as np


def analyze_text(filepath):
    analyzer = SentimentIntensityAnalyzer()
    with open(filepath, 'w') as s:
        s.write('positive sentiment: compound score >= 0.05, neutral sentiment: (compound score > -0.05) and (compound '
                'score < 0.05), negative sentiment: compound score <= -0.05\n')
        with open('../saved_texts/cnn_articles.csv', 'r') as f:
            reader = csv.reader(f)
            counter = 1
            for row in reader:
                vs = analyzer.polarity_scores(row[4])
                s.write(f"On {row[0][:10]}, the article '{row[1]}' has a sentiment score of {str(vs)}\n")
                print(f'{counter} done', end="\r")
                counter += 1


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
    aggregate_scores('sentiment_scores/cnn_sentiment_scores_vader.txt')
