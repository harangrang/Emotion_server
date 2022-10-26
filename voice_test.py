from __future__ import division

import re
import sys
from gtts import gTTS
from google.cloud import speech


import pygame as pg
import pyaudio
import vlc
import time


from six.moves import queue

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
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

            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,

            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True

        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)
def play_music(music_file, volume=0.8):
    freq = 16000    
    bitsize = -16   
    channels = 1    
    buffer = 1024 * 2

    pg.mixer.init(freq, bitsize, channels, buffer)
    pg.mixer.music.set_volume(volume)
    clock = pg.time.Clock()
    try:
        pg.mixer.music.load(music_file)
        print("Music file {} loaded!".format(music_file))
    except pg.error:
        print("File {} not found! ({})".format(music_file, pg.get_error()))
        return
    pg.mixer.music.play()
    while pg.mixer.music.get_busy():
        clock.tick(10)

    pg.quit()

def play_voice(file):
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(file)
    player.set_media(media)

    player.play()
    time.sleep(4)


global quest1_cnt, quest2_cnt
quest1_cnt = 0
quest2_cnt = 0
def listen_print_loop(responses):
    global quest1_cnt, quest2_cnt

    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

            quest1 = "안녕하세요"
            quest2 = "잘있어"

            talk1 = "반갑습니다 오늘하루 어떠셧나요?"
            talk2 = "안녕히가세요"

            listen_str = transcript + overwrite_chars
            answer_str = ""
            listen_str.replace(" ","")
            listen_str.replace('안녕하세요',' ',quest1_cnt)
            listen_str.replace('잘있어','',quest2_cnt)
            print("DEBUG" + listen_str)
            print("1:"+str(quest1_cnt))
            print("2:"+str(quest2_cnt))
            print("1::" + listen_str in quest1)
            if listen_str in quest1 :
                answer_str = talk1
                quest1_cnt +=1
            elif listen_str in quest2 :
                answer_str = talk2
                quest2_cnt +=1

 
            if answer_str != "" :
                tts = gTTS(
                    text=answer_str,
                    lang='ko', slow=False
                )
                tts.save('./ex_ko.mp3')
                #play_music('./ex_ko.mp3',0.8)
                play_voice('../../OneDrive/바탕 화면/Desktop/ex_ko.mp3')
            transcript = ""
            overwrite_chars= ""
            num_chars_printed = 0
        else:
            print(transcript + overwrite_chars) 
            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0


def main():
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "ko-KR"  # a BCP-47 language tag

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

        listen_print_loop(responses)


if __name__ == "__main__":
    main()
# [END speech_transcribe_streaming_mic]
