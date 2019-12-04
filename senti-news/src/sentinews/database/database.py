import os

from dotenv import load_dotenv
from sqlalchemy import Column, String, DateTime, Text, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sentinews.models.vader import VaderAnalyzer
from sentinews.models.textblob import TextBlobAnalyzer

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


def updateArticle(article, url=None, datetime=None, title=None, news_co=None, text=None, vader_positive=None,
                  vader_negative=None, vader_neutral=None, vader_compound=None, textblob_polarity=None,
                  textblob_subjectivity=None, textblob_classification=None, textblob_p_pos=None, textblob_p_neg=None):
    if url is not None: article.url = url
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


def analyze_table(session):
    start_time = time.perf_counter()
    va = VaderAnalyzer()
    end_time1 = time.perf_counter()
    tb = TextBlobAnalyzer()
    end_time2 = time.perf_counter()
    results = session.query(Article). \
        filter(or_(Article.vader_compound == None, Article.textblob_polarity == None)). \
        all()
    end_time3 = time.perf_counter()
    # once = False
    for row in results:
        # if once: break
        # else: once = True
        title = row.title
        vader_dict = va.evaluate([title], all_scores=True)[0]
        tb_dict = tb.evaluate([title], all_scores=True)[0]
        tb_nb_dict = tb.evaluate([title], all_scores=True, naive=True)[0]
        updateArticle(row, vader_compound=vader_dict['compound'],
                      vader_positive=vader_dict['pos'],
                      vader_negative=vader_dict['neg'],
                      vader_neutral=vader_dict['neu'],
                      textblob_polarity=tb_dict['polarity'],
                      textblob_subjectivity=tb_dict['subjectivity'],
                      textblob_classification=tb_nb_dict['classification'],
                      textblob_p_neg=tb_nb_dict['p_neg'],
                      textblob_p_pos=tb_nb_dict['p_pos'])
        print("updated "+title)
        session.commit()
        end_time4 = time.perf_counter()
        logging.info(f"1:{end_time1-start_time}")
        logging.info(f"2:{end_time2-end_time1}")
        logging.info(f"3:{end_time3-end_time1}")
        logging.info(f"4:{end_time4-end_time3}")
    return results


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
