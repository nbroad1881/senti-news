import pathlib

import psycopg2
import pandas as pd

conn = psycopg2.connect(database="nicholasbroad", host='localhost',port='5432',user='nicholasbroad',password='')
cur = conn.cursor()

print('database opened')
CNN_DIR_PATH = pathlib.Path('../saved_texts/CNN/text_info/')
CNN_INFO_FILENAME = 'CNN_INFO.csv'
TEST_ROW = " INSERT INTO vader_scores VALUES('www.lol.com', '21092', 'Trump Sux', 'cnn', 'aasdf', 1, 3, 4, 5)"

def create_sentiment_db(cur):
    cur.execute("""CREATE TABLE sentiments (
                url TEXT UNIQUE PRIMARY KEY,
                date TEXT,
                title TEXT,
                publisher TEXT,
                content TEXT,
                vader_positive REAL,
                vader_neutral  REAL,
                vader_negative  REAL,
                vader_compound  REAL)""")
    conn.commit()
    cur.close()
    conn.close()



def transfer_from_csv(csv_filepath):
    col_names = ['url', 'date', 'id', 'title', 'lexicon', 'vader']
    cnn_info = pd.read_csv(csv_filepath, header=None, names=col_names)
    cnn_info.loc[:, 'vader'] = cnn_info['vader'].str.slice(start=18).astype(float)
    cnn_info.drop(columns=['id', 'lexicon'], inplace=True)
    conn = sqlite3.connect('vader_test.db')
    cnn_info.to_sql('vader_test.db', conn,  if_exists='replace')


# if __name__ == '__main__':
    # transfer_from_csv((CNN_DIR_PATH / CNN_INFO_FILENAME))