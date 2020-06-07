from flask import request, abort, make_response, jsonify
import logging
import requests
from requests.exceptions import HTTPError, ConnectTimeout, ReadTimeout, SSLError
import math
from config.tsurls import GOOGLE_URL
from config.tskeys import G_DIRECTIONS_API_KEY
from config.tsconfig import HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT
import time

# initialize logger for app
logger = logging.getLogger(__name__)

# main function used for API endpoint /ts-geo/route/{start_addr}/{end_addr}
def getRoute(start_addr,end_addr,trans_id):
    # clean input and log for debug mode
    logger.debug(f'[trans_id: {trans_id}, start_addr: {start_addr}')
    logger.debug(f'[trans_id: {trans_id}, end_addr: {end_addr}')
    clean_start_addr = cleanInput(start_addr)
    logger.debug(f'[trans_id: {trans_id}, clean_start_addr: {clean_start_addr}')
    clean_end_addr = cleanInput(end_addr)
    logger.debug(f'[trans_id: {trans_id}, clean_start_addr: {clean_end_addr}')

    message = {"start_addr":clean_start_addr,"end_addr":clean_end_addr}

    resp = callDirectionsAPI(clean_start_addr, clean_end_addr, trans_id)
    message['status'] = resp['status']
    if resp['status'] == 'OK':
        message['data'] = resp['data']

    return message

def cleanInput(addr):
    return addr.strip().replace(" ","+")

def callDirectionsAPI(start_addr,end_addr,trans_id):
    message = {"status":"EMPTY"}
    if start_addr != "" and end_addr != "":
        # find way to restrict US address lookup.
        guri = f"""/maps/api/directions/json?origin={start_addr}&destination={end_addr}&key={G_DIRECTIONS_API_KEY}"""
        full_url = f'{GOOGLE_URL}{guri}'
        service = "/maps/api/directions"
        logger.info(f'Calling {service} API [trans_id: {trans_id}]')
        response = ''

        try:
            response = requests.get(url=full_url, timeout=(HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT))
        except HTTPError as http_err:
            logger.error(f'HTTP error occured on {service} [trans_id: {trans_id}]: {http_err}')
            eres = jsonify(status="ERROR", error_code="HTTP_ERROR", error_message="There was an HTTP_ERROR on the server side.")
            abort(make_response(eres,500))
        except SSLError as ssl_err:
            logger.error(f'SSL error occured on {service} [trans_id: {trans_id}]: {ssl_err}')
            eres = jsonify(status="ERROR", error_code="SSL_ERROR", error_message="There was an SSL_ERROR on the server side.")
            abort(make_response(eres,500))
        except ConnectTimeout as ct:
            logger.error(f'Connection Timeout occured on {service} [trans_id: {trans_id}]: {ct}')
            eres = jsonify(status="ERROR", error_code="HTTP_CONNECT_TIMEOUT", error_message="The server was unable to make an HTTP connection.")
            abort(make_response(eres,500))
        except ReadTimeout as rt:
            logger.error(f'Read Timeout occured on {service} [trans_id: {trans_id}]: {rt}')
            eres = jsonify(status="ERROR", error_code="HTTP_READ_TIMEOUT", error_message="The server took too long to respond.")
            abort(make_response(eres,500))
        except Exception as err:
            logger.error(f'Error occured on {service} [trans_id: {trans_id}]: {err}')
            eres = jsonify(status="ERROR", error_code="UNKNOWN_ERROR", error_message="An unknown error occured on the server side.")
            abort(make_response(eres,500))
        else :
            if response.status_code == 200:
                jres = response.json()
                message['status'] = jres['status']
                logger.info(f'[trans_id: {trans_id}, status: {jres["status"]}]')

                if jres['status'] == 'OK':
                    message['data'] = parseJsonResponse(jres,trans_id)

    return message

def parseJsonResponse(jres,trans_id):
    # used to parse required data from directions API
    data = {}
    route = jres['routes'][0]

    data['distance'] = route['legs'][0]['distance']['value']
    data['duration'] = route['legs'][0]['duration']['value']
    data['polyline'] = route['overview_polyline']['points']
    data['geo_spacers'] = analyzeGeoCoordinates(decode_polyline(data['polyline']),data['distance'],data['duration'],trans_id)

    return data

def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append((lat / 100000.0, lng / 100000.0))

    return coordinates

def calculateDistance(latlong_a, latlong_b):
    EARTH_CIRCUMFERENCE = 6378137

    lat1, lon1 = latlong_a
    lat2, lon2 = latlong_b

    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dLon / 2) * math.sin(dLon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = EARTH_CIRCUMFERENCE * c

    return (d/1609.344) # should return miles

def analyzeGeoCoordinates(geo_list,distance,duration,trans_id):
    miles_traveled = 0.0
    hours = round(duration/3600) # rounds to the nearest hour.
    miles = round(distance/1609.344)
    avg_miles = 60.0 # round(miles/hours)
    new_geo_list = []
    new_geo_list.append(geo_list[0])

    i = 1
    while i < len(geo_list):
        offset = i - 1
        miles_traveled += calculateDistance(geo_list[offset], geo_list[i])
        if miles_traveled >= avg_miles:
            new_geo_list.append(geo_list[i])
            miles_traveled = 0
        elif (i+1) == len(geo_list) and miles_traveled >= 35.0: # used to add the last coordinate
            new_geo_list.append(geo_list[i])
        elif (i+1) == len(geo_list) and miles_traveled < 35.0:
            new_geo_list.pop()
            new_geo_list.append(geo_list[i])

        i += 1

    return new_geo_list
