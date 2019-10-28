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

    print(f'Out of {len(neg)} articles, the medians are neg = {np.median(neg)},'
          f' neu = {np.median(neu)}, pos = {np.median(pos)}, and compound = {np.median(com)})')


if __name__ == '__main__':
    aggregate_scores('sentiment_scores/cnn_sentiment_scores_vader.txt')
