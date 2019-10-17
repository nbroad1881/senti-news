from flask import render_template
from candpred import app

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Miguel'}
    return render_template('base.html', title='Home')