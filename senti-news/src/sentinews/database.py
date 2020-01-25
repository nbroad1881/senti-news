"""
This file is in charge of communicating with the database, both in creating tables and modifying values.
class Article is a template for what each row in the database should be.
class DataBase connects to the database listed in .env
"""

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

DB_URL = os.environ.get("DB_URL")

Base = declarative_base()


class Article(Base):
    """
    Article extends the declarative_base() class from sqlalchemy. The variables will become the column names and the
    __tablename__ will be the name of the table created in the database. The url of the article is the unique
    identifier in the database.
    """
    __tablename__ = 'articles'
    url = Column(Text, primary_key=True)
    datetime = Column(DateTime)
    title = Column(Text)
    news_co = Column(String(50))
    text = Column(Text)
    vader_p_pos = Column(Float)
    vader_p_neg = Column(Float)
    vader_p_neu = Column(Float)
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
        """
        :return: A dictionary of column names as keys and their values as values.
        :rtype: dict
        """
        return str({
            'url': self.url,
            'datetime': self.datetime,
            'title': self.title,
            'news_co': self.news_co,
            'text': self.text,
            'vader_p_pos': self.vader_p_pos,
            'vader_p_neg': self.vader_p_neg,
            'vader_p_neu': self.vader_p_neu,
            'vader_compound': self.vader_compound,
            'textblob_p_pos': self.textblob_p_pos,
            'textblob_p_neg': self.textblob_p_neg,
            'lstm_p_neu': self.lstm_p_neu,
            'lstm_p_pos': self.lstm_p_pos,
            'lstm_p_neg': self.lstm_p_neg,
        })


class DataBase:
    """
    Connects to a database that will store the article and sentiment information.
    The database url is specified in the .env file. The url should have the form
    ${DB_DIALECT}://${DB_USERNAME}:${DB_PASSWORD}@${DB_ENDPOINT}:${DB_PORT}/${DB_NAME}
    Can create an table named "articles" for storing articles.
    Can query "articles" for certain articles, searching by url.

    """

    def __init__(self, database_url=None):

        self.database_url = database_url or DB_URL
        self.engine = create_engine(self.database_url)
        self.urls = self.get_urls()

    def create_article_table(self):
        """
        If there is not a table already in the database, it creates one and returns True.
        If the table already exists, it returns False. The table name is taken from the __table__
        variable from any subclass of Base. In this case, from Article which has
        __table__ = 'articles

        :return: True if table created, False if table already exists.
        :rtype: bool
        """
        if self.engine.dialect.has_table(self.engine, Article.__tablename__):
            return False
        Base.metadata.create_all(self.engine)
        return True

    def get_session(self):
        """
        Get the sqlalchemy.orm.session.Session object for this database.
        The session can be used for querying, adding/deleting rows, and committing the database changes
        to be permanent. From database_url, an engine can be made. From an engine, a sessionmaker can be made.
        From a sessionmaker, a Session can be made.
        :return: sqlalchemy.orm.session.Session object
        :rtype: sqlalchemy.orm.session.Session
        """
        Session = sessionmaker(bind=self.engine)
        return Session()

    def find_row(self, url):
        """
        Returns result if found, otherwise None
        :param url: url to be checked if it is the database
        :type url: str
        :return: search result if found, None if not found.
        :rtype: sentinews.database.Article or None
        """
        session = self.get_session()
        result = session.query(Article).filter(Article.url == url).first()
        session.close()
        return result

    def add_article_info(self, url, datetime, title, news_co, text=''):
        """
        Adds a row of article info to the database associated with this instance. It does NOT
        add sentiment scores.
        :param url: url of article
        :type url: str
        :param datetime: date of article
        :type datetime: datetime.datetime
        :param title: title of article
        :type title: str
        :param news_co: news company that published the article
        :type news_co: str
        :param text: text content of the article
        :type text: str
        :return: True if the row is added successfully, False if it is already in the database.
        :rtype: bool
        """
        if url in self.urls:
            logging.info(f"{title} already in db -- skipping")
            return False
        logging.info(f"{title} added to db")
        article = Article(url=url, datetime=datetime, title=title, news_co=news_co, text=text)
        session = self.get_session()
        session.add(article)
        session.commit()
        session.close()
        self.urls.add(url)
        return True

    def delete_row(self, url):
        """
        Deletes the row in the database by url.
        :param url: url to find in the database
        :type url: str
        :return: True if deleted, False if not found in database
        :rtype: bool
        """
        session = self.get_session()
        result = self.find_row(url)
        if result is None:
            session.close()
            return False
        session.delete(result)
        session.commit()
        session.close()
        self.urls.remove(url)
        return True

    def get_urls(self):
        """
        Returns a set of urls from the database.
        :return: set of urls from database
        :rtype: set
        """
        session = self.get_session()
        urls = set(item[0] for item in session.query(Article.url).all())
        session.close()
        return urls

    def in_table(self, url):
        """
        Returns True if the url is in the instance set of urls. Faster than find_row() which queries the
        database. find_row() also returns all the information.
        :param url: url to check
        :type url: str
        :return: True if in set, otherwise False
        :rtype: bool
        """
        return url in self.urls

    def update_article(self,
                       article,
                       session,
                       url=None,
                       datetime=None,
                       title=None,
                       news_co=None,
                       text=None,
                       vader_p_pos=None,
                       vader_p_neg=None,
                       vader_p_neu=None,
                       vader_compound=None,
                       textblob_p_pos=None,
                       textblob_p_neg=None,
                       lstm_p_pos=None,
                       lstm_p_neu=None,
                       lstm_p_neg=None):
        """
        Updates given article with the passed values. Commits to database after updating.
        :param session: session that the article was pulled from
        :type session: sqlalchemy.orm.session.Session
        :param article: article object to be updated
        :type article: sentinews.database.Article
        :param url: url of article
        :type url: str
        :param datetime: datetime of article publishing
        :type datetime: datetime.datetime
        :param title: title of article
        :type title: str
        :param news_co: news company that published article
        :type news_co: str
        :param text: text content of article
        :type text: str
        :param vader_p_pos: positive vader sentiment score of article title [0-1]
        :type vader_p_pos: float
        :param vader_p_neg: negative vader sentiment score of article title [0-1]
        :type vader_p_neg: float
        :param vader_p_neu: neutral vader sentiment score of article title [0-1]
        :type vader_p_neu: float
        :param vader_compound: compound vader sentiment score of article title [0-1]
        :type vader_compound: float
        :param textblob_p_pos: probability that title has positive sentiment
        :type textblob_p_pos: float
        :param textblob_p_neg: probability that title has negative sentiment
        :type textblob_p_neg: float
        :param lstm_p_pos: probability of title having positive sentiment
        :type lstm_p_pos: float
        :param lstm_p_neu: probability of title having neutral sentiment
        :type lstm_p_neu: float
        :param lstm_p_neg: probability of title having negative sentiment
        :type lstm_p_neg: float
        :return: None
        :rtype: NoneType
        """
        if url is not None:
            self.urls.remove(article.url)
            article.url = url
            self.urls.add(url)
        if datetime is not None: article.datetime = datetime
        if title is not None: article.title = title
        if news_co is not None: article.news_co = news_co
        if text is not None: article.text = text
        if vader_p_pos is not None: article.vader_p_pos = vader_p_pos
        if vader_p_neg is not None: article.vader_p_neg = vader_p_neg
        if vader_p_neu is not None: article.vader_p_neu = vader_p_neu
        if vader_compound is not None: article.vader_compound = vader_compound
        if textblob_p_pos is not None: article.textblob_p_pos = textblob_p_pos
        if textblob_p_neg is not None: article.textblob_p_neg = textblob_p_neg
        if lstm_p_pos is not None: article.lstm_p_pos = lstm_p_pos
        if lstm_p_neu is not None: article.lstm_p_neu = lstm_p_neu
        if lstm_p_neg is not None: article.lstm_p_neg = lstm_p_neg
        session.commit()

    def calculate_scores(self):
        """
        Looks at table from self.session() and checks for a null sentiment score in:
        1.) vader_p_pos
        2.) textblob_p_pos
        3.) lstm_p_pos

        If there are null values, it will use all models (vader, textblob, lstm) to evaluate each row.
        The LTSM model is loaded from the path and filename provided in the environment variables
        'LSTM_PKL_MODEL_DIR' and 'LSTM_PKL_FILENAME'
        :return: Results that were changed
        :rtype: list of sentinews.database.Article objects
        """
        va = VaderAnalyzer()
        tb = TextBlobAnalyzer()
        lstm = LSTMAnalyzer()
        session = self.get_session()
        results = session.query(Article). \
            filter(or_(Article.vader_p_pos == None,
                       Article.textblob_p_pos == None,
                       Article.lstm_p_pos == None)).all()
        logging.info(f"{len(results)} rows to update.")
        for row in results:
            title = row.title
            vader_dict = va.evaluate(title)
            tb_dict = tb.evaluate(title)
            lstm_dict = lstm.evaluate(title)
            self.update_article(row,
                                session=session,
                                vader_compound=vader_dict['compound'],
                                vader_p_pos=vader_dict['p_pos'],
                                vader_p_neg=vader_dict['p_neg'],
                                vader_p_neu=vader_dict['p_neu'],
                                textblob_p_neg=tb_dict['p_neg'],
                                textblob_p_pos=tb_dict['p_pos'],
                                lstm_p_neu=lstm_dict['p_neu'],
                                lstm_p_pos=lstm_dict['p_pos'],
                                lstm_p_neg=lstm_dict['p_neg'],
                                )

        session.close()
        logging.info("Table is up-to-date")
        return results


if __name__ == '__main__':
    db = DataBase()
    db.calculate_scores()
