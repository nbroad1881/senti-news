from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv

analyzer = SentimentIntensityAnalyzer()
with open('cnn_sentiment_scores_vader.txt', 'w') as s:
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
