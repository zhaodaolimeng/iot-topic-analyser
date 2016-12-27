from urllib import parse
import requests


def reverse_geo(lat, lng):
    # Base URL being accessed
    url = 'https://maps.googleapis.com/maps/api/geocode/json'

    # Dictionary of query parameters (if any),'51.546735,-0.056651',
    parms = {
       'latlng': str(lat) + ',' + str(lng),
       'key': 'AIzaSyAtuP8wQ-d-Y6ApsC2NDaSdS5Zdq4cz4Gk'
    }
    # Encode the query string
    querystring = parse.urlencode(parms)

    # Make a GET request and read the response
    r = requests.get(url+'?' + querystring)
    data = r.json()
    try:
        ret = data["results"][0]["geometry"]["location_type"]
        return ret
    except Exception:
        return "UNKNOWN"
