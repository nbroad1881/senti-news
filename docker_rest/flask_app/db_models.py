from flask_app.flask_db import db


class DBArticle(db.Model):
    __tablename__ = 'articles'
    url = db.Column(db.Text, primary_key=True)
    datetime = db.Column(db.DateTime)
    title = db.Column(db.Text)
    news_co = db.Column(db.String(50))
    text = db.Column(db.Text)
    vader_p_pos = db.Column(db.Float)
    vader_p_neg = db.Column(db.Float)
    vader_p_neu = db.Column(db.Float)
    vader_compound = db.Column(db.Float)
    textblob_p_pos = db.Column(db.Float)
    textblob_p_neg = db.Column(db.Float)
    lstm_p_neu = db.Column(db.Float)
    lstm_p_pos = db.Column(db.Float)
    lstm_p_neg = db.Column(db.Float)


descriptions = DBArticle().query.column_descriptions[0]['entity'].__dict__.keys()

# get rid of dunder variables (__tablename__, __module__, etc.)
COLUMN_NAMES = [column_name for column_name in descriptions if column_name[0] != '_']