from urllib import parse
import requests
import requests.exceptions
import time


def reverse_geo(lat, lng):
    """
    :param lat:
    :param lng:
    :return: osm_id
    """
    url = 'http://nominatim.openstreetmap.org/reverse'
    parms = {
        'format': 'json',
        'lat': str(lat),
        'lon': str(lng)
    }
    querystring = parse.urlencode(parms)
    try:
        r = requests.get(url + '?' + querystring).json()
        print(r["osm_id"])
        osm_dict = {'way': 'W', 'node': 'N', 'relation': 'R'}
        return r["osm_id"], osm_dict[r["osm_type"]]
    except Exception:
        return "REVERSE_GEO_ERROR"


def lookup_place_type(osm_id, o_type):
    url = "http://nominatim.openstreetmap.org/lookup"
    parms = {
        'format': 'json',
        'osm_ids': o_type+osm_id
    }
    querystring = parse.urlencode(parms)
    r = ""
    try:
        r = requests.get(url + '?' + querystring).json()
        if r[0]["type"] == 'yes':
            return r[0]["class"]
        return r[0]["type"]
    except Exception:
        print(r)
        return "LOOKUP_ERROR"


def location_type(lat, lng):
    delay = 0.5
    min_delay = delay
    while True:
        try:
            if lat is None or lng is None:
                return "NOT_SET"
            o_id, o_type = reverse_geo(lat, lng)
            l_type = lookup_place_type(o_id, o_type)
            print("Type = " + l_type)
            delay = max(min_delay, delay/2)
            break
        except IOError:
            print("Retry...")
            delay *= 2
        except Exception:
            return "ERROR"
    return l_type
