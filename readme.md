# README
## This repository is for my project using text data from news articles to predict the popularity of presidential candidates in the 2020 United States Presidential Election.


### What
The goal of this project is to predict the popularity of each candidate.  There are currently, as of October 1, 19 Democrats and 4 Republicans in contention for the presidential nomination. Other parties and candidates will not be considered at this time. 

### How
* Use news text data to predict popularity of presidential candidates in the United States 2020 election. The news sources will have different biases and based in different regions. Initial approaches can just use lexicons, tokenization, and other rule-based approaches. Next, sentiment analysis and other NLP techniques will be used to determine whether articles are positive or negative.

Possible approaches
1.  Continuous bag of words, count vectorization, tokenization
2.  Naive Bayes

* I will first use a news API to gather large amounts of text data from various sources.
* The predictions will be compared against polls from the Economist/YouGov, Monmouth, Politico/Morning Consult, Harvard-Harris, Emerson, and Quinnipia.

### Why
* It is generally regarded as very difficult to predict the popularity of a presidential candidate, and it could be useful for the candidate or active supporters to know what makes a candidate’s popularity increase.


### Goals
1.	Create a pipeline to take text data from the news sources, clean the text data, and then analyze it using lexicons, tokenization, and other rule-based approaches.
2.	Start with just the top 5 democratic candidates right now (Biden, Warren, Sanders, Buttigieg, Harris)
3.	Build more complicated models that account for the news outlet’s bias, using NLP approaches like sentiment analysis, vectorization, and machine learning algorithms.
4.	Have an interactive user-facing product to show latest results.
