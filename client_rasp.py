# -*- coding: utf8 -*-
import cv2
import socket
import numpy as np
import time
from _thread import *
import os

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect(('192.168.0.2', 8485))

cam = cv2.VideoCapture(0)

cam.set(3, 320);
cam.set(4, 240);

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]


def speak(option, msg):
    os.system("espeak {} '{}'".format(option, msg))


option = '-s 160 -p 95 -a 200 -v ko+f3'


def recv_data(client_socket):
    while True:
        data = client_socket.recv(1024)
        str = repr(data.decode())
        if str == "angry":
            speak(option, "화남")
        elif str == "Disgusted":
            speak(option, "역겨움")
        elif str == "Fearful":
            speak(option, "무서움")
        elif str == "Happy":
            speak(option, "행복")
        elif str == "Neutral":
            speak(option, "자연스러운")
        elif str == "Sad":
            speak(option, "슬픈")
        elif str == "Surprised":
            speak(option, "놀람")

        print("recive : ", repr(data.decode()))

while True:
    ret, frame = cam.read()
    result, frame = cv2.imencode('.jpg', frame, encode_param)
    data = np.array(frame)
    stringData = data.tostring()

    s.sendall((str(len(stringData))).encode().ljust(16) + stringData)
    time.sleep(0.066)

cam.release()
