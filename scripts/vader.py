from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import csv


analyzer = SentimentIntensityAnalyzer()
with open('../texts/cnn_articles.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        vs = analyzer.polarity_scores(row[4])
        print(f"On {row[0][:10]}, the article '{row[1]}' has a sentiment score of {str(vs)}")
