from flask import request

from flask_app.flask_db import app, db
from flask_app.db_models import DBArticle, COLUMN_NAMES
from flask_app.schemas import ArticleSchema

articleSchema = ArticleSchema()


# todo: make payload because urls can't go in a url
#  or use urllib
@app.route("/article/", methods=['GET', 'POST', 'PUT'])
def article_route():
    args = request.args.to_dict()

    # Pull one article from the database by finding matching url
    if request.method == 'GET':
        # make sure url parameter passed
        if args and 'url' in args:
            # returns None if not in database
            article = DBArticle.query.filter_by(url=args['url']).first()
            if article:
                return articleSchema.dump(article), 200
            return 'Url not found', 404
        return 'Invalid parameters', 400

    # Create new article in database
    if request.method == 'POST':
        # Make sure they include the right parameters
        if args:
            for col in COLUMN_NAMES:
                if col not in args:
                    return 'Invalid parameters', 400
        else:
            return 'Invalid parameters', 400

        # Check if the article is already in the database
        if DBArticle.query.filter_by(url=args['url']).first():
            return 'Already exists, use PUT to update', 409

        # All validations passed, create article and add to database
        article = DBArticle(
            url=args['url'],
            datetime=args['datetime'],
            title=args['title'],
            news_co=args['news_co'],
            text=args['text'],
            vader_p_pos=args['vader_p_pos'],
            vader_p_neg=args['vader_p_neg'],
            vader_p_neu=args['vader_p_neu'],
            vader_compound=args['vader_compound'],
            textblob_p_pos=args['textblob_p_pos'],
            textblob_p_neg=args['textblob_p_neg'],
            lstm_p_neu=args['lstm_p_neu'],
            lstm_p_pos=args['lstm_p_pos'],
            lstm_p_neg=args['lstm_p_neg'])
        db.session.add(article)
        db.session.commit()
        return 'Article added successfully', 201

    if request.method == 'PUT':
        if args and 'url' in args:
            # returns None if not in database
            article = DBArticle.query.filter_by(url=args['url']).first()
            if article is None:
                return "Use POST to add a new article", 403
            for col in COLUMN_NAMES:
                if col in args:
                    article[col] = args[col]
            db.session.commit()
            return "Article successfully updated", 200
        return "Invalid parameters", 400

    return "Invalid request. Use GET, POST, or PUT", 400
