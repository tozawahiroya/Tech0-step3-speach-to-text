from __future__ import division


import os
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'tech0-step3-te-bd23bed77076.json'

import re
import sys

import pyaudio
from six.moves import queue

import streamlit as st
import time

global total_words
total_words = ""


st.markdown('↑　現状は押すと初期画面に戻る。MVPとしては下記にFeedback画面が表示されるイメージ')







