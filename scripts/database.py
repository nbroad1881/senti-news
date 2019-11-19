import pathlib

import pandas as pd
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Text, create_engine
from sqlalchemy.orm import sessionmaker

LOCAL_POSTGRESQL_URL = 'postgresql://nicholasbroad:@localhost:5432/nicholasbroad'

BASE_PATH = '../saved_texts/{}/text_info/{}_INFO.csv'
CNN_INFO_PATH = pathlib.Path('../saved_texts/CNN/text_info/')
CNN_INFO_FILENAME = 'CNN_INFO.csv'

NYT_INFO_PATH = pathlib.Path('../saved_texts/NYT/text_info')
NYT_INFO_FILENAME = "NYT_INFO.csv"

FOX_INFO_PATH = pathlib.Path('../saved_texts/FOX/text_info')
FOX_INFO_FILENAME = "FOX_INFO.csv"

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
    news = Column(String(50))


def create_article_db():
    Base.metadata.create_all(engine)

def add_row_to_db(url, datetime, title):
    article = Article(url=url, datetime=datetime, title=title)
    session.add(article)
    session.commit()


def transfer_from_csv(csv_filepath):
    info = pd.read_csv(csv_filepath, header=None, usecols=USE_COLS, parse_dates=[DATE_COL])

    for row_num in range(info.shape[0]):
        row = info.iloc[row_num, :]
        add_row_to_db(url=row[URL_COL], datetime=row[DATE_COL], title=row[TITLE_COL])

if __name__ == '__main__':
    engine = create_engine(LOCAL_POSTGRESQL_URL, echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    if not engine.dialect.has_table(engine, 'articles'):
        create_article_table()
    choice = input("Which news company would you like to scrape?\n"
                   "1. CNN\n"
                   "2. Fox News\n"
                   "3. NYTimes\n"
                   "4. (in future) Debug Mode\n")
    if choice in CHOICE_DICT:
        news = CHOICE_DICT[choice]
        path = pathlib.Path(BASE_PATH.format(news, news))
        transfer_from_csv(session, path, NEWS_CO_DICT[choice])
    session.close()
