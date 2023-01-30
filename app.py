from __future__ import division
from google.cloud import speech

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

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses):
    num_chars_printed = 0
    global total_words
    total_words = ""

    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(transcript)
            

        else:
            st.write(transcript + overwrite_chars)
            #ここが表示
            count=0
            if count==0:
                total_words=total_words + transcript + overwrite_chars + "\n"
                count = 1

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(発言を終了します|発言を終わります)\b", transcript, re.I):
                print("Exiting..")
                total_words=total_words.split('発言を終')[0]
                #最終引数
                break

            num_chars_printed = 0

def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "ja-JP"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses)

df_list = pd.read_csv("question_list.csv", header = None, encoding="shift-jis" )


st.title('フェルミ推定/ケース面接アプリ')
st.markdown('問題')
option = st.selectbox(
    '問題番号を選択してください',
    df_list[0])
question = ""
question = df_list[df_list[0]==option].iloc[0,1]

if st.button('出題＆録音開始'):
    st.code('質問：　' + question)
    st.error('●録音中')
    st.write("→「終了」するには「発言を終了します」と発声し、入力してください")
    main()
    st.markdown('■入力内容')
    txt = st.text_area("修正が完了したら、【Submit】ボタンを押して提出してください",total_words, height = 300)

    st.button('Submit！')
    st.markdown('↑　現状は押すと初期画面に戻る。MVPとしては下記にFeedback画面が表示されるイメージ')
    

