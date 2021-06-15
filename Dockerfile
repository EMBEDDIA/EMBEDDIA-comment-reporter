FROM python:3.8


RUN pip3 install --upgrade pip
COPY ["requirements.txt", "requirements.txt"]
RUN pip3 install -r /requirements.txt

RUN mkdir app
ADD . /app
WORKDIR /app

EXPOSE 8080

CMD ["python3", "/app/server.py", "8080"]
