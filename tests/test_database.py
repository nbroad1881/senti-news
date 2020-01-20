from datetime import datetime
import os
import re

import pytest
from dotenv import load_dotenv
from sqlalchemy.orm.session import Session

from sentinews.database import Article, DataBase


load_dotenv()


@pytest.fixture
def my_article():
    return Article(url='www.example.com',
                   datetime=datetime(2000, 1, 1),
                   title='Trump is president.',
                   news_co='Fox News',
                   text='A great article about the president.',
                   vader_positive=.1,
                   vader_negative=.2,
                   vader_neutral=.3,
                   vader_compound=.4,
                   textblob_polarity=.5,
                   textblob_subjectivity=.6,
                   textblob_classification='pos',
                   textblob_p_pos=.7,
                   textblob_p_neg=.8,
                   lstm_score=.9,
                   lstm_category='neg',
                   lstm_p_neu=-.1,
                   lstm_p_pos=-.2,
                   lstm_p_neg=-.3)


DB_ENDPOINT = os.environ.get('DB_ENDPOINT')
DB_PORT = os.environ.get('DB_PORT')
DB_USERNAME = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
DB_URL = f"postgres://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}"


@pytest.fixture(params=[DB_URL])
def database(request):
    return DataBase(database_url=request.param)


def test_create_article_table(database):
    assert database.create_article_table() is False


def test_get_session(database):
    session = database.get_session()
    assert isinstance(session, Session)



    assert re.findall(r'\@(.*)\:', str(session.get_bind()))[0] == DB_ENDPOINT
    assert re.findall(r'\:(\d+)\/', str(session.get_bind()))[0] == DB_PORT
    assert re.findall(r'\d\/(.*)\)$', str(session.get_bind()))[0] == DB_NAME


test_url = ['random.com', 'example.com', 'universe.com']
test_datetime = [datetime(2000, 1, 2), datetime(2000, 1, 3), datetime(2000, 1, 4)]
test_title = ['first title', 'second title', 'third title']
test_news_co = ['cnn', 'fox', 'new york times']
test_text = ['first piece of text', 'second piece of text', 'third piece of text']


@pytest.mark.parametrize("url, datetime_, title, news_co, text",
                         list(zip(
                             test_url,
                             test_datetime,
                             test_title,
                             test_news_co,
                             test_text,
                         )))
def test_add_find_and_delete_row(url, datetime_, title, news_co, text, database):
    database.add_row(url, datetime_, title, news_co, text)
    result = database.get_session().query(Article).filter(Article.url == url).first()
    assert result is not None
    assert result.datetime == datetime_
    assert result.title == title
    assert result.news_co == news_co
    assert result.text == text
    database.delete_row(url)
    database.close_session()
    find = database.find_row(url)
    assert find is False
    check = database.get_session().query(Article).filter(Article.url == url).first()
    assert check is None


def test_get_urls_in_table(database):
    urls = database.get_urls()
    actual_urls = database.get_session().query(Article.url).all()
    assert len(urls) == len(actual_urls)

    for url in actual_urls:
        assert(url[0] in urls)

