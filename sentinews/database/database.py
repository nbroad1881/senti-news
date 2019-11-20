import pandas as pd
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Text, create_engine
from sqlalchemy.orm import sessionmaker

LOCAL_POSTGRESQL_URL = 'postgresql://nicholasbroad:@localhost:5432/nicholasbroad'

BASE_PATH = '../saved_texts/{}/text_info/{}_INFO.csv'

URL_COL = 0
DATE_COL = 1
TITLE_COL = 2
USE_COLS = [URL_COL, DATE_COL, TITLE_COL]
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


def create_article_table():
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


def transfer_from_csv(session, csv_filepath, news_co):
    info = pd.read_csv(csv_filepath, header=None, usecols=USE_COLS, parse_dates=[DATE_COL])

    for row_num in range(info.shape[0]):
        row = info.iloc[row_num, :]
        url = row[URL_COL]
        add_row_to_db(session, url=url, datetime=row[DATE_COL], title=row[TITLE_COL], news_co=news_co)


if __name__ == '__main__':
    engine = create_engine(LOCAL_POSTGRESQL_URL)
    session = get_session(engine)
    if not engine.dialect.has_table(engine, 'articles'):
        create_article_table()

    choice = input("Which news company would you like to transfer?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n"
                   "4. (in future) Debug Mode\n")
    if choice in CHOICE_DICT:
        news = CHOICE_DICT[choice]
        path = BASE_PATH.format(news, news)
        transfer_from_csv(session, path, NEWS_CO_DICT[choice])
    session.close()
