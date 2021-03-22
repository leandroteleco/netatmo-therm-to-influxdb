#!/usr/bin/env python3

import requests
import time
import os
import json
from datetime import datetime, timezone, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import ASYNCHRONOUS

# DATA TO CONNECT AND TO RECORD MEASUREMENTS IN INFLUXDB DATABASE:
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_ORG = os.environ.get("INFLUX_ORG")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET")
INFLUX_URL = os.environ.get("INFLUX_URL")
INFLUX_TAG_VALUE_1 = os.environ.get("INFLUX_TAG_VALUE_1")
INFLUX_MEASUREMENT = os.environ.get("INFLUX_MEASUREMENT")
INFLUX_TAG_NAME_1 = os.environ.get("INFLUX_TAG_NAME_1")

# CREDENTIALS TO CONNECT WITH NETATMO API:
NETATMO_CLIENT_ID = os.environ.get("NETATMO_CLIENT_ID") 
NETATMO_CLIENT_SECRET = os.environ.get("NETATMO_CLIENT_SECRET") 
NETATMO_USERNAME = os.environ.get("NETATMO_USERNAME") 
NETATMO_PASSWORD = os.environ.get("NETATMO_PASSWORD") 
NETATMO_HOME_ID = os.environ.get("NETATMO_HOME_ID") 
NETATMO_SCOPE = "read_thermostat"
NETATMO_QUERRY_CADENCE = int(os.environ.get("NETATMO_QUERRY_CADENCE") )

netatmoAccessToken = ""
netatmoRefreshToken = ""
netatmoDatetimeToken = datetime.utcnow()
print("Welcome to Netatmo-Home.")
print("Program start date: " + str(netatmoDatetimeToken))

def getNetatmoAccessToken():
    global netatmoAccessToken
    global netatmoDatetimeToken
    global netatmoRefreshToken
    url = "https://api.netatmo.com/oauth2/token"
    payload = {"grant_type":"password", "client_id":NETATMO_CLIENT_ID, "client_secret":NETATMO_CLIENT_SECRET, "username":NETATMO_USERNAME, "password":NETATMO_PASSWORD, "scope":NETATMO_SCOPE}
    headers = {
        'Host': 'api.netatmo.com',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code != 200:
        print("ERROR: The error code is: {}".format(response.status_code))
        print("Response: " + str(response))
        print("Payload: " + str(payload))
    else:
        print("Access Token: " + response.json()["access_token"])
        print("Refresh Token: " + response.json()["refresh_token"])
        netatmoDatetimeToken = datetime.utcnow()
        netatmoAccessToken = response.json()["access_token"]
        netatmoRefreshToken = response.json()["refresh_token"]
        print("Expires in : " + str(response.json()["expires_in"]) + " / " + str(response.json()["expire_in"]))
    return response

def getNetatmoRefreshAccessToken():
    global netatmoAccessToken
    global netatmoRefreshToken
    global netatmoDatetimeToken
    url = "https://api.netatmo.com/oauth2/token"
    payload = {"grant_type":"refresh_token", "refresh_token":netatmoRefreshToken, "client_id":NETATMO_CLIENT_ID, "client_secret":NETATMO_CLIENT_SECRET}
    headers = {
        'Host': 'api.netatmo.com',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code != 200:
        print("ERROR: The error code is: {}".format(response.status_code))
        print("Response: " + str(response))
        print("Payload: " + str(payload))
    else:
        print("Access Token: " + response.json()["access_token"])
        netatmoAccessToken = response.json()["access_token"]
        print("Refresh Token: " + response.json()["refresh_token"])
        netatmoAccessToken = response.json()["refresh_token"]
        print("Expires in : " + str(response.json()["expires_in"]))
        netatmoDatetimeToken = datetime.utcnow()
        return response.json()["access_token"]


def getNetatmoHomestatus():
    global netatmoAccessToken
    if datetime.utcnow() < netatmoDatetimeToken + timedelta(minutes=60):
        url = "https://api.netatmo.com/api/homestatus?"
        payload = {"home_id":NETATMO_HOME_ID}
        headers = {'Accept': 'application/json', 'Authorization': "Bearer " + netatmoAccessToken, 'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code != 200:
            print("ERROR: The error code is: {}".format(response.status_code))
            print("Response: " + str(response))
            print("Payload: " + str(payload))
        else:
            print("Measured Temperature: " + str(response.json()["body"]["home"]["rooms"][0]["therm_measured_temperature"]) + " / Thermostat setting: " + str(response.json()["body"]["home"]["rooms"][0]["therm_setpoint_temperature"]))
    else:
        netatmoAccessToken = getNetatmoRefreshAccessToken()
        url = "https://api.netatmo.com/api/homestatus?"
        payload = {"home_id":NETATMO_HOME_ID}
        headers = {'Accept': 'application/json', 'Authorization': "Bearer " + netatmoAccessToken, 'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code != 200:
            print("ERROR: The error code is: {}".format(response.status_code))
            print("Response: " + str(netatmoAccessToken))
        else:
            print("Measured Temperature: " + str(response.json()["body"]["home"]["rooms"][0]["therm_measured_temperature"]) + " / Thermostat setting: " + str(response.json()["body"]["home"]["rooms"][0]["therm_setpoint_temperature"]))
    return response 

def getInfluxDBClient():
    try:
        influxClient = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        print("InfluxDB connection: OK -> " + INFLUX_URL + " -> " + INFLUX_ORG)
    except:
            print("ERROR: There was a problem connecting to InfluxDB.")
    return influxClient

def writeMeasurements(field, measure, write_api):
    try: 
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=[{"measurement": INFLUX_MEASUREMENT, "tags": {INFLUX_TAG_NAME_1: INFLUX_TAG_VALUE_1}, "fields": {field: measure}}])
        #print('Measure writed: ' + str(measure) + ' ' + INFLUX_TAG_NAME_1 + ' : ' + INFLUX_TAG_VALUE_1 + ' ' + INFLUX_MEASUREMENT + ' ' + INFLUX_ORG + ' ' + INFLUX_BUCKET)
    except:
        print('ERROR: There was a problem saving the measurement to the database.')

def main():
    getNetatmoAccessToken()
    influxClient_1 = getInfluxDBClient()
    write_api_1 = influxClient_1.write_api(write_options=ASYNCHRONOUS)
    try:
        while True:
            responseHomestatus = getNetatmoHomestatus()
            temperatureValue = responseHomestatus.json()["body"]["home"]["rooms"][0]["therm_measured_temperature"]
            thermostatValue = responseHomestatus.json()["body"]["home"]["rooms"][0]["therm_setpoint_temperature"]
            writeMeasurements("temperature_measured", temperatureValue, write_api_1)
            writeMeasurements("thermostat_set", thermostatValue, write_api_1)
            time.sleep(NETATMO_QUERRY_CADENCE)

    except KeyboardInterrupt:
        print("Press Ctrl-C to terminate while statement")
        pass

main()