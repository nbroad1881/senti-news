import os
import logging

from dateutil.parser import isoparse
from flask import request
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

from flask_app.flask_db import app, db
from flask_app.db_models import DBArticle, COLUMN_NAMES
from flask_app.schemas import ArticleSchema
from sentinews.models import VaderAnalyzer, LSTMAnalyzer, TextBlobAnalyzer

articleSchema = ArticleSchema()
articlesSchema = ArticleSchema(many=True)
load_dotenv()
logging.basicConfig(level=logging.DEBUG)

DB_TABLE_NAME = os.environ['DB_TABLE_NAME']
DB_URL = os.environ['DB_URL']
DB_PARSE_COLUMNS = os.environ['DB_PARSE_COLUMNS']
DB_SELECT_COLUMNS = os.environ['DB_SELECT_COLUMNS']

va = VaderAnalyzer()
tb = TextBlobAnalyzer()
lstm = LSTMAnalyzer()


# todo: make table object to avoid update error (table.c)
@app.route("/")
def home():
    return ":^)"


@app.route("/urls", methods=["GET"])
def urls():
    """
    Get all the urls in the database
    :return:
    :rtype:
    """
    articles = DBArticle.query.with_entities(DBArticle.url, DBArticle.title).all()
    return articlesSchema.jsonify(articles, many=True), 200


@app.route("/article/", methods=['GET', 'POST', 'PUT', 'DELETE'])
def article_route():
    args = request.args.to_dict()
    if args is None:
        return "No parameters given", 400

    # Pull one article from the database by finding matching url
    if request.method == 'GET':

        if 'all' in args:
            if args['all']:
                # todo: bulk article pull
                # results = pd.read_sql_table(DB_TABLE_NAME, DB_URL, parse_dates=DB_PARSE_COLUMNS, columns=DB_SELECT_COLUMNS)
                return "todo", 400

        # make sure url parameter passed
        if 'url' in args:
            # returns None if not in database
            article = DBArticle.query.filter_by(url=args['url']).first()
            if article:
                return articleSchema.dump(article), 200
            return 'Url not found', 404
        return 'Invalid parameters', 400

    # Create new article in database
    if request.method == 'POST':

        parameters = {}
        # Make sure they include the right parameters
        for col in COLUMN_NAMES:
            if col not in args:
                return 'Invalid parameters', 400
            parameters[col] = args[col]

        # Check if the article is already in the database
        if DBArticle.query.filter_by(url=args['url']).first():
            return 'Already exists, use PUT to update', 409

        # All validations passed, create article and add to database
        article = articleSchema.load(args)
        db.session.add(article)
        db.session.commit()
        return 'Article added successfully', 201

    if request.method == 'PUT':
        # returns None if not in database
        article = DBArticle.query.filter_by(url=args['url']).first()
        if article is None:
            return "Use POST to add a new article", 403
        update_article_fields(article, **args)
        db.session.commit()
        return "Article successfully updated", 200

    if request.method == 'DELETE':
        result = DBArticle.query.filter_by(url=args['url']).delete()
        db.session.commit()
        if result:
            return "Successfully deleted", 200
        return "Nothing to delete with specified url.", 204

    return "Invalid request. Use GET, POST, PUT, or DELETE with good parameters.", 400


@app.route("/analyze/<model>", methods=["GET", "POST"])
def analyze(model):
    if request.method == "POST":
        if model == 'all':
            args = request.args.to_dict()
            title = args['title']
            va_scores = va.evaluate(title)
            tb_scores = tb.evaluate(title)
            lstm_scores = lstm.evaluate(title)
            # todo: consider using dict unpacking **dict
            article = DBArticle(
                url=args['url'],
                datetime=isoparse(args['datetime']),
                title=args['title'],
                news_co=args['news_co'],
                text=args['text'],
                vader_p_pos=va_scores['p_pos'],
                vader_p_neg=va_scores['p_neg'],
                vader_p_neu=va_scores['p_neu'],
                vader_compound=va_scores['compound'],
                textblob_p_pos=tb_scores['p_pos'],
                textblob_p_neg=tb_scores['p_neg'],
                lstm_p_neu=lstm_scores['p_neu'],
                lstm_p_pos=lstm_scores['p_pos'],
                lstm_p_neg=lstm_scores['p_neg'])
            try:
                db.session.add(article)
            except IntegrityError as e:
                logging.info(f"Could not add to database error: {e}")
            db.session.commit()
            return articleSchema.dump(article), 200


def update_article_fields(article, **kwargs):
    keys = kwargs.keys()
    if 'datetime' in keys: article.datetime = kwargs['datetime']
    if 'title' in keys: article.title = kwargs['title']
    if 'news_co' in keys: article.news_co = kwargs['news_co']
    if 'text' in keys: article.text = kwargs['text']
    if 'vader_p_pos' in keys: article.vader_p_pos = kwargs['vader_p_pos']
    if 'vader_p_neg' in keys: article.vader_p_neg = kwargs['vader_p_neg']
    if 'vader_p_neu' in keys: article.vader_p_neu = kwargs['vader_p_neu']
    if 'vader_compound' in keys: article.vader_compound = kwargs['vader_compound']
    if 'textblob_p_pos' in keys: article.textblob_p_pos = kwargs['textblob_p_pos']
    if 'textblob_p_neg' in keys: article.textblob_p_neg = kwargs['textblob_p_neg']
    if 'lstm_p_pos' in keys: article.lstm_p_pos = kwargs['lstm_p_pos']
    if 'lstm_p_neu' in keys: article.lstm_p_neu = kwargs['lstm_p_neu']
    if 'lstm_p_neg' in keys: article.lstm_p_neg = kwargs['lstm_p_neg']
