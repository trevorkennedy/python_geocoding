__author__ = 'trevor.kennedy'

import csv
import json
import xml.dom.minidom
import urllib.request as urllib
from collections import namedtuple

Address = namedtuple('Address', ('provider', 'address', 'city', 'state', 'zip', 'lat', 'long', 'use', 'year', 'lot', 'sqft', 'bath', 'bed', 'value'))


# ---------- ZILLOW API ----------
zwskey = "X1-ZWz1chwxis1xxxxxxxxxx"

def get_element_by_tag(doc, field_name):
    return doc.getElementsByTagName(field_name)[0].firstChild.data if len(
        doc.getElementsByTagName(field_name)) > 0 else None


def get_zillow_data(address, city, state):
    # Construct the URL
    url = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?'
    url += 'zws-id=%s&address=%s&citystatezip=%s, %s' % (zwskey, address, city, state)
    url = url.replace(' ', '+')

    # Parse resulting XML
    doc = xml.dom.minidom.parseString(urllib.urlopen(url).read())
    code = doc.getElementsByTagName('code')[0].firstChild.data

    # Code 0 means success; otherwise, there was an error
    if code != '0': return None

    # Extract the info about this property
    try:
        zipcode = get_element_by_tag(doc, 'zipcode')
        use = get_element_by_tag(doc, 'useCode')
        year = get_element_by_tag(doc, 'yearBuilt')
        lot = get_element_by_tag(doc, 'lotSizeSqFt')
        sqft = get_element_by_tag(doc, 'finishedSqFt')
        bath = get_element_by_tag(doc, 'bathrooms')
        bed = get_element_by_tag(doc, 'bedrooms')
        value = get_element_by_tag(doc, 'amount')
        street = get_element_by_tag(doc, 'street')
        city = get_element_by_tag(doc, 'city')
        state = get_element_by_tag(doc, 'state')
        lat = get_element_by_tag(doc, 'latitude')
        long = get_element_by_tag(doc, 'longitude')
    except:
        return None

    return Address('ZILLOW', street, city, state, zipcode, lat, long, use, year, lot, sqft, bath, bed, value)


# ---------- GOOGLE API ----------
key = 'AIzaSyDKv72al83_zPFfo9xxxxxxxxxxxxxx'


def build_google_url(address, city, state):
    addr = address + '%2C+' + city + '%2C+' + state
    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    url += 'key=%s&sensor=false&address=%s' % (key, addr)
    return url.replace(' ', '+')


def get_google_josn(url):
    data = json.loads(urllib.urlopen(url).read().decode('utf-8'))
    return data


def parse_google_json(data):
    if data['status'] == 'OK':
        place = data['results'][0]

        geo_type = place['geometry']['location_type']

        if geo_type == "APPROXIMATE" or geo_type == "GEOMETRIC_CENTER":
            return None  # Exact address was not found

        latitude = place['geometry']['location']['lat']
        longitude = place['geometry']['location']['lng']

        for c in place['address_components']:
            if c['types'] == ['street_number']:
                no = c['short_name']
            elif c['types'] == ['route']:
                address = c['short_name']
            elif c['types'] == ['postal_code']:
                zip = c['short_name']
            elif c['types'] == ["locality", "political"]:
                city = c['short_name']
            elif c['types'] == ["administrative_area_level_1", "political"]:
                state = c['short_name']

        return Address('GOOGLE', no + ' ' + address, city, state, zip, latitude, longitude, None, None, None, None, None, None, None)
    else:
        return None


def get_google_data(address, city, state):
    url = build_google_url(address, city, state)
    data = get_google_josn(url)
    return parse_google_json(data)


# ---------- SmartyStreets API ----------
authid = 'e68689e9-f102-aa91-746c-xxxxxxxxxx'
authtoken = '6YmG5gLxkap0bMiJiR1SbZ%2F7jqYo1v2CW4gXeYrbxxxxxxxxxxx'


def build_smarty_url(address, city, state, zip):
    url = 'https://api.smartystreets.com/street-address?'
    url += 'auth-id=%s&auth-token=%s&street=%s&city=%s&state=%s&zipcode=%s' % (
    authid, authtoken, address, city, state, zip)
    return url.replace(' ', '%20')


def get_smarty_json(url):
    data = json.loads(urllib.urlopen(url).read().decode('utf-8'))
    return data


def parse_smarty_json(data):
    if len(data) > 0:
        response = data[0]
        address = response['delivery_line_1']
        city = response['components']['city_name']
        state = response['components']['state_abbreviation']
        zip = response['components']['zipcode']
        lat = response['metadata']['latitude']
        long = response['metadata']['longitude']
        use = response['metadata']['rdi']
        return Address('SMARTYSTREETS', address, city, state, zip, lat, long, use, None, None, None, None, None, None)
    else:
        return None


def get_smarty_data(address, city, state, zip):
    url = build_smarty_url(address, city, state, zip)
    data = get_smarty_json(url)
    return parse_smarty_json(data)

#data=get_zillow_data('410 BRIARWOOD CT', 'VERNON HILLS', 'IL')
#print(data)
#data=get_google_data('410 BRIARWOOD CT', 'VERNON HILLS', 'IL')
#print(data)
#data=get_smarty_data('410 BRIARWOOD CT', 'VERNON HILLS', 'IL', '60061')
#print(data)

def main(in_file, out_file):
    with open(in_file) as r_file:
        r = csv.reader(r_file)
        headers = next(r)
        with open(out_file, 'w', newline='') as w_file:
            w = csv.writer(w_file, quoting=csv.QUOTE_MINIMAL)
            for row in r:
                data=get_zillow_data(row[0], row[1], row[2])
                if data is not None:
                    w.writerow(data)

main(r'address input.csv', r'geocoded output.csv')