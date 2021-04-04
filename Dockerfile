FROM python:3.7-slim
ADD requirements.txt /app/requirements.txt
RUN apt-get update && apt-get install gcc g++ -y
RUN apt-get install libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 -y
RUN pip3 install -r /app/requirements.txt
WORKDIR /app
COPY . .
CMD [ "python3", "server.py"]