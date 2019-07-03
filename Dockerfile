FROM python:3.7-alpine

RUN apk --no-cache add build-base

WORKDIR /usr/src/app

COPY requirements.txt teufel-mqtt.py ./

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./teufel-mqtt.py" ]
