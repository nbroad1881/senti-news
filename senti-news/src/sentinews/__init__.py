import wget
import pathlib
import os

from dotenv import load_dotenv

load_dotenv()


os.environ['LSTM_PKL_FILENAME'] = 'lstm.pkl'

current_dir = pathlib.Path(__file__).parent
g = list((current_dir / 'lstm_pkls').glob('**/*.pkl'))
if os.environ.get('LSTM_PKL_DIR_PATH') is None and len(g) > 0:
    os.environ['LSTM_PKL_DIR_PATH'] = str(g[0].parent)
    os.environ['LSTM_PKL_FILENAME'] = g[0].name
# elif len(g) == 0:
#     url = os.environ['LSTM_PKL_URL']
#     os.environ['LSTM_PKL_DIR_PATH'] = current_dir / 'lstm_pkls'
#     print('No pkl file found, downloading now...')
#     wget.download(url, os.environ.get('LSTM_PKL_DIR_PATH') / os.environ.get("LSTM_PKL_FILENAME"))
