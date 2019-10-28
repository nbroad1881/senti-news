from textblob import TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
import csv

with open('cnn_sentiment_scores_textblob_NB.txt', 'w') as s:
    with open('../saved_texts/cnn_articles.csv', 'r') as f:
        reader = csv.reader(f)
        counter = 1
        for row in reader:
            blob = TextBlob(row[4], analyzer=NaiveBayesAnalyzer())
            s.write(f"On {row[0][:10]}, the article '{row[1]}' has a sentiment score of {str(blob.sentiment)}\n")
            print(f'{counter} done', end="\r")
            counter += 1
