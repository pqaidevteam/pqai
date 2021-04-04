FROM python:3.7-slim-stretch
WORKDIR /app
RUN apt-get update && apt-get install gcc g++ -y
RUN apt-get install libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 -y
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --progress-bar on
COPY . .
CMD [ "python3", "server.py"]