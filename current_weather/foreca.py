#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# Fetch and parse current weather observations from www.foreca.fi
#
# v0.9 2017-02-19
# License: MIT

import datetime
import json
import logging
import re
import requests
import sys

def javascript_to_json(string):
    # Quote keys
    string = re.sub(r'([\'"]?)(\w+)([\'"]?):', r'"\2":', string)
    # Single quotes to double quotes
    string = re.sub(r': ?[\']([^\']*)[\']', r': "\1"', string)
    # Add double quotes to unquoted values
    string = re.sub(r': ?([\w.:+-]+)', r': "\1"', string)
    return string


def foreca_get_observations(url):
    try:
        r = requests.get(url)
        if (r.status_code != 200):
            logging.error("Failed to retrieve {}: status {}".format(url, r.status_code))
            return (None, None)
    except:
        logging.exception("Failed to retrive {}".format(url))
        return (None, None)
    #print(r.text)
    try:
        stationsJS = re.findall("var stations = (.*?);", r.text, re.DOTALL)[0]
        observationsJS = re.findall("var observations = (.*?);", r.text, re.DOTALL)[0]
    except:
        logging.exception("Failed to parse {}".format(url))
        return (None, None)
    stations = json.loads(javascript_to_json(stationsJS))
    observations = json.loads(javascript_to_json(observationsJS))
    return (stations, observations)

def parse_observations(stations, observations):
    data = []
    stationNames = {}
    today = datetime.date.today()
    for s in stations:
        stationNames[s["id"]] = s["n"]
    for oid in observations:
        o = observations[oid]
        stationName = stationNames[oid]

        # Parse date
        dayMonth = re.findall("[0-9]+", o["date"])
        day = int(dayMonth[0])
        month = int(dayMonth[1])
        year = today.year
        # Check if observation was from last year
        if month == 12 and today.month == 1:
            year = year - 1
        hourMin = re.findall("[0-9]+", o["time"])
        hour = int(hourMin[0])
        minute = int(hourMin[1])
        dt = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

        nullval = "null"
        record = {
                "station": stationName,
                "timestamp": dt,
                "temperature":
                    o["temp"] if "temp" in o else nullval,
                "temperature_feels_like":
                    o["flike"] if "flike" in o else nullval,
                "windspeed":
                    o["winds"] if "winds" in o else nullval,
                "windalt":
                    o["windalt"] if "windalt" in o else nullval,
                "wx":
                    o["wx"] if "wx" in o else nullval,
                "pressure":
                    o["pres"] if "pres" in o else nullval,
                "humidity":
                    o["rhum"] if "rhum" in o else nullval,
                "dewpoint":
                    o["dewp"] if "dewp" in o else nullval,
                "visibility":
                    o["vis"] if "vis" in o else nullval,
                "visibility_unit":
                    o["visunit"] if "visunit" in o else nullval,
                "snow_depth":
                    o["snow"]["depth"] if "snow" in o and o["snow"] is not None and "depth" in o["snow"] else nullval,
                }
        data.append(record)
    return data

def pretty_print(data):
    for o in data:
        print(u"""
{}
  time:         {}
  weathertype:  {}
  temperature:  {}°C
  feels_like:   {}°C
  wind:         {} {}
  barometer:    {} hPa
  dewpoint:     {}°C
  humidity:     {}%
  visibility:   {} {}
  snow_depth:   {} cm""".format(
            o["station"],
            o["timestamp"],
            o["wx"],
            o["temperature"],
            o["temperature_feels_like"],
            o["windspeed"], o["windalt"],
            o["pressure"],
            o["dewpoint"],
            o["humidity"],
            o["visibility"],
            o["visibility_unit"] if o["visibility_unit"] != "null" else "km",
            o["snow_depth"]))

def main():
    if len(sys.argv) < 2:
        print("usage: {} http://www.foreca.fi/Finland/Helsinki\n".format(sys.argv[0]))
        return
    url = sys.argv[1]
    stations, observations = foreca_get_observations(url)
    parsedObservations = parse_observations(stations, observations)
    pretty_print(parsedObservations)

if __name__ == "__main__":
    main()
