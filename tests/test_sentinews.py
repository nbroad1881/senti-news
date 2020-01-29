"""
Tests to make sure functionality of database.py is working.
"""

from datetime import datetime, timedelta, timezone
import os
import re

from dateutil.parser import isoparse
import pytest
from dotenv import load_dotenv
from sqlalchemy.orm.session import Session

from sentinews.database import Article, DataBase
from sentinews.models import TextBlobAnalyzer, VaderAnalyzer, LSTMAnalyzer
from sentinews.scraping.api_scraper import ArticleSource, CNN, FOX, NEWSAPI, NYT, DEFAULT_START_DATE, DEFAULT_END_DATE

load_dotenv()


class TestDataBase:

    @pytest.fixture
    def article(self, ):
        """
        Article object. Currently unused in any test.
        :return:  Example Article object
        :rtype: sentinews.database.Article
        """
        return Article(url='www.example.com',
                       datetime=datetime(2000, 1, 1),
                       title='Trump is president.',
                       news_co='Fox News',
                       text='A great article about the president.',
                       vader_p_pos=.1,
                       vader_p_neg=.2,
                       vader_p_neu=.3,
                       vader_compound=.4,
                       textblob_p_pos=.7,
                       textblob_p_neg=.8,
                       lstm_p_neu=-.1,
                       lstm_p_pos=-.2,
                       lstm_p_neg=-.3)

    @pytest.fixture()
    def database(self):
        """
        DataBase object to be used in other tests.
        :return: DataBase with default configuration from environment variables.
        :rtype: sentinews.DataBase
        """
        return DataBase()

    def test_create_article_table(self, database):
        """
        Test for
        create_article_table()
        The function returns False if there is already a table.
        There should already be a table so it should False.
        :param database: DataBase fixture
        :type database: sentinews.DataBase
        """
        assert database.create_article_table() is False

    def test_get_session(self, database):
        """
        Test for:
        get_session()
        It should get the session information from the database specified in the environment variables.
        """
        session = database.get_session()
        # Make sure it is getting a Session object.
        assert isinstance(session, Session)

        # Test if the database url in the session matches the environment variables
        assert re.search(r'@(.*):', str(session.get_bind())).group(1) == os.environ.get('DB_ENDPOINT')
        assert re.search(r':(\d+)/', str(session.get_bind())).group(1) == os.environ.get('DB_PORT')
        assert re.search(r'\d/(.*)\)$', str(session.get_bind())).group(1) == os.environ.get('DB_NAME')

    # Data to be parametrized
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
    def test_add_find_and_delete_row(self, url, datetime_, title, news_co, text, database):
        """
        Test for:
        add_row()
        find_row()
        delete_row()
        """
        # Start by deleting row just in case it is already in the database
        database.delete_row(url)

        # Start by adding a dummy article
        database.add_article_info(url, datetime_, title, news_co, text)
        # Get that article from the database
        result = database.get_session().query(Article).filter(Article.url == url).first()

        # Assert that the article from the database exists and matches the information just added
        assert result is not None
        assert result.datetime == datetime_
        assert result.title == title
        assert result.news_co == news_co
        assert result.text == text

        # Use find_row to get same information and check if it is the same
        find = database.find_row(url)
        assert result.datetime == find.datetime
        assert result.title == find.title
        assert result.news_co == find.news_co
        assert result.text == find.text

        # Delete the row from the database
        database.delete_row(url)

        # Since it was deleted, it shouldn't be able to find the article
        find = database.find_row(url)
        assert find is None

    def test_get_urls_in_table(self, database):
        """
        Test for:
        get_urls()
        See if function gets urls that are in the database.
        :param database: DataBase that is storing article information.
        :type database: sentinews.database.DataBase
        """
        urls = database.get_urls()
        actual_urls = database.get_session().query(Article.url).all()
        # Are there the same number of urls
        assert len(urls) == len(actual_urls)

        # Is each url actually in the database
        for url in actual_urls:
            assert (url[0] in urls)

    def test_add_info(self, database):
        """
        Test for:
        in_table()
        add_article_info()
        calculate_scores()

        See if the information passed to add_article_info() ends up in the database.
        See if the null sentiment scores get filled with real sentiment scores.
        :param database: DataBase that is storing article information.
        :type database: sentinews.database.DataBase
        """
        url = 'test.com'
        # delete row in case it is already in database
        database.delete_row(url)
        database.add_article_info(url,
                                  datetime.today(),
                                  'title',
                                  'news_co',
                                  'text')
        # Check if the url is in the database
        assert database.in_table(url) is True

        # Pull that information back and make sure there are no sentiment scores
        row = database.find_row(url)
        assert row is not None
        assert row.vader_p_pos is None
        assert row.vader_p_neg is None
        assert row.vader_p_neu is None
        assert row.vader_compound is None
        assert row.textblob_p_pos is None
        assert row.textblob_p_neg is None
        assert row.lstm_p_pos is None
        assert row.lstm_p_neu is None
        assert row.lstm_p_neg is None

        # Calculate the sentiment scores and add them to database.
        database.calculate_scores()
        # Make sure that each score is not None
        row = database.find_row(url)
        assert row.vader_p_pos is not None
        assert row.vader_p_neg is not None
        assert row.vader_p_neu is not None
        assert row.vader_compound is not None
        assert row.textblob_p_pos is not None
        assert row.textblob_p_neg is not None
        assert row.lstm_p_pos is not None
        assert row.lstm_p_neu is not None
        assert row.lstm_p_neg is not None

        # Delete the dummy row and make sure it is out of the database
        database.delete_row(url)
        assert database.find_row(url) is None


class TestModels:
    """
    Test models in sentinews.models.py
    """
    sample_sentence = "This is a great day."

    # Create a model fixture for each.
    @pytest.fixture
    def textblob_analyzer(self):
        return TextBlobAnalyzer()

    @pytest.fixture
    def vader_analyzer(self):
        return VaderAnalyzer()

    # LSTMAnalyzer needs to have the LSTM model directory and filename to load.
    @pytest.fixture
    def lstm_analyzer(self):
        return LSTMAnalyzer()

    # Testing TextBlobAnalyzer
    @pytest.mark.parametrize("sentence", [sample_sentence])
    def test_textblob_evaluate(self, sentence, textblob_analyzer):
        sentiment = textblob_analyzer.evaluate(sentence)

        # Make sure sentiment is within range
        # These are probabilities, so values should be between 0 and 1.
        assert 0 <= sentiment['p_pos'] <= 1
        assert 0 <= sentiment['p_neg'] <= 1

        # All outcomes must add to 1
        assert 1 - 1e5 < sentiment['p_pos'] + sentiment['p_neg'] < 1 + 1e5

    # Testing VaderAnalyzer
    @pytest.mark.parametrize("sentence", [sample_sentence])
    def test_vader_evaluate(self, sentence, vader_analyzer):
        sentiment = vader_analyzer.evaluate(sentence)

        # Make sure sentiment is within range
        # These are probabilities, so values should be between 0 and 1.
        assert 0 <= sentiment['p_neg'] <= 1
        assert 0 <= sentiment['p_pos'] <= 1
        assert 0 <= sentiment['p_neu'] <= 1

        # Probabilities must add to 1
        assert 1 - 1e5 < sentiment['p_pos'] + sentiment['p_neg'] + sentiment['p_neu'] < 1 + 1e5

        # Compound score uses proprietary algorithm and is between -1 and 1
        assert -1 <= sentiment['compound'] <= 1

    # Testing LSTMAnalyzer
    @pytest.mark.parametrize("sentence", [sample_sentence])
    def test_lstm_evaluate(self, sentence, lstm_analyzer):
        sentiment = lstm_analyzer.evaluate(sentence)

        # Make sure sentiment is within range
        # These are probabilities, so values should be between 0 and 1.
        assert 0 <= sentiment['p_neg'] <= 1
        assert 0 <= sentiment['p_pos'] <= 1
        assert 0 <= sentiment['p_neu'] <= 1

        # Probabilities must add to 1
        assert 1 - 1e5 < sentiment['p_pos'] + sentiment['p_neg'] + sentiment['p_neu'] < 1 + 1e5


class TestScraper:

    @pytest.fixture
    def cnn(self):
        return CNN(interactive=False, start_date=None, end_date=None)\

    @pytest.fixture
    def nyt(self):
        return NYT(interactive=False, start_date=None, end_date=None)

    @pytest.fixture
    def fox(self):
        return FOX(interactive=False, start_date=None, end_date=None)

    def test_init(self):
        """
        Check to see if an improper date is given, the defaults will be used.
        :return:
        :rtype:
        """
        start_date = '2019-01-01'
        end_date = '2020-01-01'
        custom_cnn = CNN(interactive=False, start_date=start_date, end_date=end_date)
        custom_nyt = NYT(interactive=False, start_date=start_date, end_date=end_date)
        custom_fox = FOX(interactive=False, start_date=start_date, end_date=end_date)
        assert custom_cnn.start_date == DEFAULT_START_DATE
        assert custom_cnn.end_date == DEFAULT_END_DATE

        assert custom_nyt.start_date == DEFAULT_START_DATE
        assert custom_nyt.end_date == DEFAULT_END_DATE

        assert custom_fox.start_date == DEFAULT_START_DATE
        assert custom_fox.end_date == DEFAULT_END_DATE

        # Check if it can handle end date coming before start date
        start_date = '2020-01-20'
        end_date = '2020-01-01'

        custom_cnn = CNN(interactive=False, start_date=start_date, end_date=end_date)
        custom_nyt = NYT(interactive=False, start_date=start_date, end_date=end_date)
        custom_fox = FOX(interactive=False, start_date=start_date, end_date=end_date)
        assert custom_cnn.start_date == DEFAULT_START_DATE
        assert custom_cnn.end_date == DEFAULT_END_DATE

        assert custom_nyt.start_date == DEFAULT_START_DATE
        assert custom_nyt.end_date == DEFAULT_END_DATE

        assert custom_fox.start_date == DEFAULT_START_DATE
        assert custom_fox.end_date == DEFAULT_END_DATE


    yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1)
    date_strings = [yesterday.isoformat(),
                    (yesterday + timedelta(days=10)).isoformat(),
                    'not a date',
                    yesterday.isoformat(),
                    yesterday.isoformat()]
    afters = [None,
              None,
              None,
              yesterday + timedelta(days=5),
              yesterday - timedelta(days=2)]
    # Results of the check
    assertion = [True, False, False, False, True]

    @pytest.mark.parametrize("date_strings, afters, assertion",
                             list(zip(date_strings, afters, assertion)))
    def test_is_valid_date(self, date_strings, afters, assertion):

        assert ArticleSource.is_valid_date(date_string=date_strings,
                                           after=afters) == assertion

    titles = ['Only trump',
              'only biden',
              'only warren',
              'only sanders',
              'only BuTTigieg',
              'only haRRis',
              'trump and biden',
              'biden. warren. harris,'
              'trump biden warren sanders harris buttigieg',
              'a bunch of nonsense not related']
    assertion = [False, False, False, False, False, False, True, True, True, False]

    @pytest.mark.parametrize("title, assertion", list(zip(titles, assertion)))
    def test_improper_title(self, title, assertion):
        """
        Testing if the title check method works. It should return true when
        there is one and only one candidate's name in the title.
        :param title: Title to be checked for validity
        :type title: str
        :param assertion: used as base truth for title validity
        :type assertion: bool
        """
        assert ArticleSource.improper_title(title) == assertion
