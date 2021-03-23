FROM alpine:latest

RUN apk add --no-cache python3-dev py-pip
RUN pip3 install --upgrade pip

WORKDIR /app

COPY . /app

RUN pip3 --no-cache-dir install -r requirements.txt

CMD ["python3", "src/netatmo-therm-to-influx.py"]