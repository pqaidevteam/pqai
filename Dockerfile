FROM python:3.7-slim-stretch
WORKDIR /app
RUN apt-get update && apt-get install gcc g++ -y
RUN apt-get install libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 -y
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --progress-bar on
COPY config config
COPY core core
COPY docs docs
COPY tests tests
COPY auth.py auth.py
COPY .gitignore .gitignore
COPY CONTRIBUTING.md CONTRIBUTING.md
COPY README.md README.md
COPY server.py server.py
COPY user-ratings.tsv user-ratings.tsv

CMD [ "python3", "server.py"]