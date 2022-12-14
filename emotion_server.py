# -*- coding: utf-8 -*-
import socket
import cv2
import numpy as np
import time
import threading
import argparse
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import playsound
import pygame
import os
import vlc
from gtts import gTTS

global voice_flag, count
count = 0
voice_flag = 0
# socket에서 수신한 버퍼를 반환하는 함수
def recvall(sock, count):
    # 바이트 문자열
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def plot_model_history(model_history):
    """
    Plot Accuracy and Loss curves given the model_history
    """
    fig, axs = plt.subplots(1,2,figsize=(15,5))
    # summarize history for accuracy
    axs[0].plot(range(1,len(model_history.history['accuracy'])+1),model_history.history['accuracy'])
    axs[0].plot(range(1,len(model_history.history['val_accuracy'])+1),model_history.history['val_accuracy'])
    axs[0].set_title('Model Accuracy')
    axs[0].set_ylabel('Accuracy')
    axs[0].set_xlabel('Epoch')
    axs[0].set_xticks(np.arange(1,len(model_history.history['accuracy'])+1),len(model_history.history['accuracy'])/10)
    axs[0].legend(['train', 'val'], loc='best')
    # summarize history for loss
    axs[1].plot(range(1,len(model_history.history['loss'])+1),model_history.history['loss'])
    axs[1].plot(range(1,len(model_history.history['val_loss'])+1),model_history.history['val_loss'])
    axs[1].set_title('Model Loss')
    axs[1].set_ylabel('Loss')
    axs[1].set_xlabel('Epoch')
    axs[1].set_xticks(np.arange(1,len(model_history.history['loss'])+1),len(model_history.history['loss'])/10)
    axs[1].legend(['train', 'val'], loc='best')
    fig.savefig('plot.png')
    plt.show()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


ap = argparse.ArgumentParser()
ap.add_argument("--mode",help="train/display")
mode = ap.parse_args().mode
if mode == None:
    mode = "display"
mode = "display"
# Define data generators
train_dir = 'data/train'
val_dir = 'data/test'

num_train = 28709
num_val = 7178
batch_size = 64
num_epoch = 50

HOST = '192.168.0.2'
PORT = 8485


train_datagen = ImageDataGenerator(rescale=1. / 255)
val_datagen = ImageDataGenerator(rescale=1. / 255)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(48, 48),
    batch_size=batch_size,
    color_mode="grayscale",
    class_mode='categorical')

validation_generator = val_datagen.flow_from_directory(
    val_dir,
    target_size=(48, 48),
    batch_size=batch_size,
    color_mode="grayscale",
    class_mode='categorical')

# Create the model
model = Sequential()

model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48, 48, 1)))
model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(1024, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(7, activation='softmax'))


def play_voice(text):
    global voice_flag, count
    if voice_flag == 0 :
        voice_flag = 1
        tts = gTTS(
            text=text,
            lang='ko', slow=False
        )
        tts.save('./'+ str(count) +'.mp3')
        pygame.mixer.init()
        pygame.mixer.music.load('./'+ str(count) +'.mp3')
        pygame.mixer.music.play()
        time.sleep(4)
        count+=1
        voice_flag = 0


# If you want to train the same model or try other models, go for this
if mode == "train":
    model.compile(loss='categorical_crossentropy',optimizer=Adam(lr=0.0001, decay=1e-6),metrics=['accuracy'])
    model_info = model.fit_generator(
            train_generator,
            steps_per_epoch=num_train // batch_size,
            epochs=num_epoch,
            validation_data=validation_generator,
            validation_steps=num_val // batch_size)
    plot_model_history(model_info)
    model.save_weights('model.h5')


elif mode == "display":
    # TCP 사용
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')

    # 서버의 아이피와 포트번호 지정
    #s.bind((HOST, PORT))
    print('Socket bind complete')

    # 클라이언트의 접속을 기다린다. (클라이언트 연결을 10개까지 받는다)
    #s.listen(10)
    print('Socket now listening')

    # 연결, conn에는 소켓 객체, addr은 소켓에 바인드 된 주소
    #conn, addr = s.accept()

    model.load_weights('model.h5')

    #cv2.ocl.setUseOpenCL(False)
    emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}
    cap = cv2.VideoCapture(0)
    cap.set(3, 320)
    cap.set(4, 240)
    while True:
        # client에서 받은 stringData의 크기 (==(str(len(stringData))).encode().ljust(16))
        #length = recvall(conn, 16)
        #stringData = recvall(conn, int(length))
        #data = np.fromstring(stringData, dtype='uint8')

        # data를 디코딩한다.
        #frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        ret, frame = cap.read()
        facecasc = cv2.CascadeClassifier('./haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = facecasc.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y - 50), (x + w, y + h + 10), (255, 0, 0), 2)
            roi_gray = gray[y:y + h, x:x + w]
            cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray, (48, 48)), -1), 0)
            prediction = model.predict(cropped_img)
            maxindex = int(np.argmax(prediction))
            cv2.putText(frame, emotion_dict[maxindex], (x + 20, y - 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255),
                        2, cv2.LINE_AA)
            # 0: "Angry",
            # 1: "Disgusted",
            # 2: "Fearful",
            # 3: "Happy",
            # 4: "Neutral",
            # 5: "Sad",
            # 6: "Surprised"
            answer_str =""
            if maxindex == 0:
                answer_str = "화남"
            if maxindex == 1:
                answer_str = "역겨움"
            elif maxindex == 2:
                answer_str = "절망"
            elif maxindex == 3:
                answer_str = "행복"
            elif maxindex == 4:
                answer_str = "기본표정"
            elif maxindex == 5:
                answer_str = "슬픔"
            elif maxindex == 6:
                answer_str = "놀람"


            # play_music('./ex_ko.mp3',0.8)
            #play_voice('./ex_ko.mp3')
            t = threading.Thread(target=play_voice, args=(answer_str,))
            t.start()

        cv2.imshow('Video', cv2.resize(frame, (320, 240), interpolation=cv2.INTER_CUBIC))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()




