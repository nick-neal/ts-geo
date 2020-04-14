from flask import request
import logging
import requests
from requests.exceptions import HTTPError
import math

# initialize logger for app
logger = logging.getLogger(__name__)

# set constant vars
GOOGLE_URL = 'https://maps.googleapis.com'
# !!! SETUP IN CONFIG !!!
G_DIRECTIONS_API_KEY = 'AIzaSyCjkHjeLVDf4h0fmwrS4miRp1Yd5PY4SYw'

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
        logger.info(f'Calling /maps/api/directions API [trans_id: {trans_id}]')
        response = ''

        try:
            response = requests.get(full_url)

            response.raise_for_status()
        except HTTPError as http_err:
            logger.error(f'HTTP error occured for [trans_id: {trans_id}]: {http_err}')
            message['status'] = "HTTP_ERROR"
        except Exception as err:
            logger.error(f'Error occured for [trans_id: {trans_id}]: {err}')
            message['status'] = "UNKNOWN_ERROR"
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
    data['geo_spacers'] =  analyzeGeoCoordinates(decode_polyline(data['polyline']),data['distance'],data['duration'],trans_id)

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
    # used to analyze distance between coordinates
    # distances is in meters
    # duration is in seconds

    hours = round(duration/3600) # rounds to the nearest hour.
    miles = round(distance/1609.344)

    geo_list_offset = round(len(geo_list)/hours)
    mile_avg = round(miles/hours)
    print(len(geo_list))

    new_geo_list = []
    new_geo_list.append(geo_list[0])
    i = 0

    while i < len(geo_list):
        glo = i+geo_list_offset

        if glo >= len(geo_list):
            new_geo_list.append(geo_list[-1])
            break

        while True:
            if glo >= len(geo_list):
                new_geo_list.append(geo_list[-1])
                i=len(geo_list)
                break
            if round(calculateDistance(geo_list[i],geo_list[glo])) >= mile_avg:
                i = glo
                new_geo_list.append(geo_list[glo])
                break
            else:
                glo += 1
                i += 1

    return new_geo_list
