import os
import logging

from dotenv import load_dotenv
from sqlalchemy import Column, String, DateTime, Text, Float, create_engine, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sentinews.models import VaderAnalyzer
from sentinews.models import TextBlobAnalyzer
from sentinews.models import LSTMAnalyzer

load_dotenv()

logging.basicConfig(level=logging.INFO)

DB_ENDPOINT = os.environ.get('DB_ENDPOINT')
DB_PORT = os.environ.get('DB_PORT')
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
DB_URL = f"postgres://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()

"""
This file is in charge of communicating with the database, both in creating tables and storing
results.
"""


class Article(Base):
    __tablename__ = 'articles'
    url = Column(Text, primary_key=True)
    datetime = Column(DateTime)
    title = Column(Text)
    news_co = Column(String(50))
    text = Column(Text)
    vader_positive = Column(Float)
    vader_negative = Column(Float)
    vader_neutral = Column(Float)
    vader_compound = Column(Float)
    textblob_polarity = Column(Float)
    textblob_subjectivity = Column(Float)
    textblob_classification = Column(String(10))
    textblob_p_pos = Column(Float)
    textblob_p_neg = Column(Float)
    lstm_score = Column(Float)
    lstm_category = Column(String(15))
    lstm_p_neu = Column(Float)
    lstm_p_pos = Column(Float)
    lstm_p_neg = Column(Float)

    def __repr__(self):
        return str({
            'url': self.url,
            'datetime': self.datetime,
            'title': self.title,
            'news_co': self.news_co,
            'text': self.text,
            'vader_positive': self.vader_positive,
            'vader_negative': self.vader_negative,
            'vader_neutral': self.vader_neutral,
            'vader_compound': self.vader_compound,
            'textblob_polarity': self.textblob_polarity,
            'textblob_subjectivity': self.textblob_subjectivity,
            'textblob_classification': self.textblob_classification,
            'textblob_p_pos': self.textblob_p_pos,
            'textblob_p_neg': self.textblob_p_neg,
            'lstm_score': self.lstm_score,
            'lstm_category': self.lstm_category,
            'lstm_p_neu': self.lstm_p_neu,
            'lstm_p_pos': self.lstm_p_pos,
            'lstm_p_neg': self.lstm_p_neg,
        })


class DataBase:

    def __init__(self, database_url=None):

        self.database_url = database_url or DB_URL

        self.engine = create_engine(self.database_url)
        self.session = self.get_session(database_url=self.database_url)
        self.urls = set(self.get_urls())

    def create_article_table(self):
        """
        If there is not a table already in the database, it creates one and returns True.
        If the table already exists, it returns False.
        :return: True if table created, False if table already exists.
        :rtype: Boolean.
        """
        if self.engine.dialect.has_table(self.engine, Article.__tablename__):
            return False
        Base.metadata.create_all(self.engine)
        return True

    def get_session(self, database_url=None, echo=False):
        database_url = database_url or self.database_url
        Session = sessionmaker(bind=create_engine(database_url, echo=echo))
        return Session()

    def find_row(self, url):
        return self.session.query(Article).filter(Article.url == url).first()

    def add_row(self, url, datetime, title, news_co, text=''):
        if url in self.urls:
            logging.info(f"{title} already in db -- skipping")
            return False
        logging.info(f"{title} added to db")
        article = Article(url=url, datetime=datetime, title=title, news_co=news_co, text=text)
        self.session.add(article)
        self.session.commit()
        self.urls.add(url)
        return True

    def delete_row(self, url):
        result = self.session.query(Article). \
            filter(Article.url == url).first()
        self.session.delete(result)
        self.session.commit()

    def get_urls(self):
        return [item[0] for item in self.session.query(Article.url).all()]

    def in_table(self, url):
        return url in self.urls

    def updateArticle(self, article, url=None, datetime=None, title=None, news_co=None, text=None, vader_positive=None,
                      vader_negative=None, vader_neutral=None, vader_compound=None, textblob_polarity=None,
                      textblob_subjectivity=None, textblob_classification=None, textblob_p_pos=None,
                      textblob_p_neg=None, lstm_category=None, lstm_p_pos=None, lstm_p_neu=None, lstm_p_neg=None):
        if url is not None:
            article.url = url
            self.urls.add(url)
        if datetime is not None: article.datetime = datetime
        if title is not None: article.title = title
        if news_co is not None: article.news_co = news_co
        if text is not None: article.text = text
        if vader_positive is not None: article.vader_positive = vader_positive
        if vader_negative is not None: article.vader_negative = vader_negative
        if vader_neutral is not None: article.vader_neutral = vader_neutral
        if vader_compound is not None: article.vader_compound = vader_compound
        if textblob_polarity is not None: article.textblob_polarity = textblob_polarity
        if textblob_subjectivity is not None: article.textblob_subjectivity = textblob_subjectivity
        if textblob_classification is not None: article.textblob_classification = textblob_classification
        if textblob_p_pos is not None: article.textblob_p_pos = textblob_p_pos
        if textblob_p_neg is not None: article.textblob_p_neg = textblob_p_neg
        if lstm_category is not None: article.lstm_category = lstm_category
        if lstm_p_pos is not None: article.lstm_p_pos = lstm_p_pos
        if lstm_p_neu is not None: article.lstm_p_neu = lstm_p_neu
        if lstm_p_neg is not None: article.lstm_p_neg = lstm_p_neg
        self.session.commit()

    def analyze_table(self):
        """
        Looks at self.session's table and checks for null sentiment scores.
        If there are null values, it will use every model to evaluate each row.
        :return: Results that were changed
        :rtype: list of sentinews.database.Article objects
        """
        va = VaderAnalyzer()
        tb = TextBlobAnalyzer()
        lstm = LSTMAnalyzer(model_dir=os.environ.get('LSTM_PKL_MODEL_DIR'),
                            model_name=os.environ.get('LSTM_PKL_FILENAME'))
        results = self.session.query(Article). \
            filter(or_(Article.vader_compound == None,
                       Article.textblob_polarity == None,
                       Article.lstm_category == None)).all()
        logging.info(f"{len(results)} rows to update.")
        for row in results:
            title = row.title
            vader_dict = va.evaluate(title, all_scores=True)
            tb_dict = tb.evaluate(title, all_scores=True, naive=False)
            tb_nb_dict = tb.evaluate(title, all_scores=True, naive=True)
            lstm_dict = lstm.evaluate(title)
            self.updateArticle(row, vader_compound=vader_dict['compound'],
                               vader_positive=vader_dict['pos'],
                               vader_negative=vader_dict['neg'],
                               vader_neutral=vader_dict['neu'],
                               textblob_polarity=tb_dict['polarity'],
                               textblob_subjectivity=tb_dict['subjectivity'],
                               textblob_classification=tb_nb_dict['classification'],
                               textblob_p_neg=tb_nb_dict['p_neg'],
                               textblob_p_pos=tb_nb_dict['p_pos'],
                               lstm_category=lstm_dict['category'],
                               lstm_p_neu=lstm_dict['p_neu'],
                               lstm_p_pos=lstm_dict['p_pos'],
                               lstm_p_neg=lstm_dict['p_neg'],
                               )


        logging.info("Table is up-to-date")
        return results

    def close_session(self):
        self.session.close()

    def fill_null(self):
        self.analyze_table()
        self.close_session()


if __name__ == '__main__':
    db = DataBase()
    db.analyze_table()
    db.close_session()
