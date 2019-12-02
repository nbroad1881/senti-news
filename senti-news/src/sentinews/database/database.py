import os

from dotenv import load_dotenv
from sqlalchemy import Column, String, DateTime, Text, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')


NEWS_CO_DICT = {
    '1': 'CNN',
    '2': 'Fox News',
    '3': 'New York Times'
}

CHOICE_DICT = {
    '1': 'CNN',
    '2': 'FOX',
    '3': 'NYT'
}

Base = declarative_base()


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

class Score(Base):
    __tablename__ = 'scores'
    url = Column(Text, primary_key=True)
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


def create_article_table():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

def create_scores_table():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)

def add_row_to_db(session, url, datetime, title, news_co, text=''):
    """
    Return true if successfully added, else false
    :param session:
    :param url:
    :param datetime:
    :param title:
    :param news_co:
    :param text:
    :return:
    """
    if in_table(session, url):
        return False
    article = Article(url=url, datetime=datetime, title=title, news_co=news_co, text=text)
    session.add(article)
    session.commit()
    return True


def get_session(database_url, echo=False):
    Session = sessionmaker(bind=create_engine(database_url, echo=echo))
    return Session()


def get_urls(session):
    return [item[0] for item in session.query(Article.url).all()]


def in_table(session, url):
    return session.query(Article).get(url) is not None


if __name__ == '__main__':
    engine = create_engine(DATABASE_URL)
    session = get_session(DATABASE_URL)
    if not engine.dialect.has_table(engine, 'articles'):
        create_article_table()

    choice = input("Which news company would you like to transfer?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n"
                   "4. (in future) Debug Mode\n")
    session.close()
