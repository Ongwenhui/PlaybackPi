FROM ubuntu:18.04
RUN apt-get update && apt-get install -y  locales
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y rpi.gpio
RUN apt-get update && apt-get install -y build-essential
RUN apt-get update && apt-get install -y make
RUN apt-get update && apt-get install -y python3-pip
RUN apt-get update && apt-get install -y python3-dev python3-setuptools
RUN apt-get update && apt-get install -y python3-requests
RUN apt-get update && apt-get install -y libi2c-dev
RUN apt-get update && apt-get install -y python-smbus
RUN apt-get update && apt-get install -y python3-smbus
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN apt-get update && apt-get install -y python-opencv
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN apt-get update && apt-get install -y libssl-dev
RUN apt-get update && apt-get install -y cmake
RUN python3 -m pip install scikit-build
RUN python3 -m pip install awsiotsdk
RUN apt-get update && apt-get install -y build-essential libssl-dev libffi-dev python-dev
RUN apt-get update && apt-get install -y libportaudio2
RUN apt-get update && apt-get install -y libsndfile-dev
RUN apt-get update && apt-get install -y libasound-dev
RUN apt-get update && apt-get install -y pulseaudio
RUN python3 -m pip install soundfile
RUN python3 -m pip install SoundFile
RUN python3 -m pip install sounddevice
RUN python3 -m pip install AWSIoTPythonSDK
RUN python3 -m pip install numpy
COPY . /playback
RUN make /playback
CMD ["python3" , "/playback/mqttindocker.py"]