import boto3
import folium
import numpy as np
from IPython.display import HTML
from math import sin, cos, sqrt, atan2, radians
import datetime

radius = 2


def gps_one(lat, lon):
    mapit = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker(location=[lat, lon],
                  popup='OBD Initial Location (ID): <br> 65615765277',
                  fill_color='#43d9de',
                  tooltip="Initial location",
                  radius=radius).add_to(mapit)
    folium.Circle([lat, lon],
                  radius=radius,
                  fill=True,
                  ).add_to(mapit)
    mapit.save('./GeoMaps/current_0_location.html')
    HTML('<iframe src=./GeoMaps/current_0_location.html width=700 height=450></ifrme>')


def gps_main(lat, lon, lat_live, lon_live):
    # approximate radius of earth in km
    R = 6373.0
    # ------------------------------------------------
    lat1 = radians(float(lat))
    lon1 = radians(float(lon))
    # ------------------------------------------------
    print("Initial Device Latitude : ", lat)
    print("Initial Device Longitude: ", lon)

    lat2 = radians(float(lat_live))
    lon2 = radians(float(lon_live))
    # ------------------------------------------------

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    print("Result:")
    print("In KM.   : ", distance, "km")
    print("In meters: ", distance * 1000, "m")
    cli = boto3.client('s3')
    cli.put_object(
        Body=str(distance * 1000),
        Bucket='ec2-obd2-bucket',
        Key='GPS/Distance/OBD2--{}.txt'.format(str(datetime.datetime.now())))

    if distance * 1000 <= float(radius):
        print("OBD device is under given area")
    else:
        print("OBD device is NOT under given area")

    map_obd = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker(location=[lat, lon], fill_color='#43d9de', radius=radius).add_to(map_obd)
    if distance * 1000 <= float(radius):
        folium.Marker(location=[lat_live, lon_live],
                      popup='OBD Device No: <br> 65615765277',
                      # icon=folium.Icon(icon="cloud", color='green'),
                      tooltip="OBD Device",
                      radius=radius).add_to(map_obd)
    else:
        folium.Marker(location=[lat_live, lon_live],
                      popup='OBD Device No: <br> 65615765277',
                      # icon=folium.Icon(icon="cloud", color='red'),
                      tooltip="OBD Device",
                      radius=radius).add_to(map_obd)

    folium.Circle([lat, lon],
                  radius=radius,
                  fill=True,
                  ).add_to(map_obd)
    map_obd.add_child(folium.LatLngPopup())
    map_obd.save('./GeoMaps/current_OBD_current_location.html')
    HTML('<iframe src=./GeoMaps/current_OBD_current_location.html width=700 height=450></ifrme>')
