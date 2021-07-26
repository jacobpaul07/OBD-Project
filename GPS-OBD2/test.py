
import socket
import datetime
from obd_gps import gps_one, gps_main
from Utils.calculate_engine_RPM import calculate_engine_RPM


def convert_LOGIN_data(login_data):
    """
    Function that'll convert Raw LOGIN data to Readable JSON Object
    """
    # --------- Headers for final dictionary ---------
    HEADERS = ['Live/Memory', 'Signature', 'IMEI', 'Message Type', 'Sequence No', 'CHECKSUM']

    # Result dictionary
    result = {}

    # --------- Data Processing ---------
    for index, header in enumerate(HEADERS):
        result[header] = login_data[index]

    return result


def convert_GPS_data(gps_data):
    """
    Function that'll convert Raw GPS data to Readable JSON Object
    """

    if len(gps_data) == 23:
        # --------- Headers for final dictionary ---------
        HEADERS = ['Live/Memory', 'Signature', 'IMEI', 'Message Type', 'Sequence No', 'Time (GMT)', 'Date',
                   'valid/invalid', 'Latitude', 'Longitude', 'Speed (knots)', 'Angle of motion', 'Odometer (KM)',
                   'Internal battery Level (Volts)', 'Signal Strength', 'Mobile country code', 'Mobile network code',
                   'Cell id', 'Location area code',
                   '#Ignition(0/1), RESERVED ,Harsh Braking / Acceleration//Non(0/2/3),Main power status(0/1)',
                   'Over speeding', 'Signature', 'CHECKSUM']

        # Result dictionary
        result = {}

        # --------- Data Processing ---------
        for index, header in enumerate(HEADERS):
            result[header] = gps_data[index]

        return result

    else:
        # --------- Headers for final dictionary ---------
        HEADERS = ['Live/Memory', 'Signature', 'IMEI', 'Message Type', 'Sequence No', 'Time (GMT)', 'Date',
                   'valid/invalid', 'Latitude', 'North/South', 'Longitude', 'East/West', 'Speed (knots)',
                   'Angle of motion', 'Odometer (KM)', 'Internal battery Level (Volts)', 'Signal Strength',
                   'Mobile country code', 'Mobile network code', 'Cell id', 'Location area code',
                   '#Ignition(0/1), RESERVED ,Harsh Braking / Acceleration//Non(0/2/3),Main power status(0/1)',
                   'Over speeding', 'Signature', 'CHECKSUM']

        # Result dictionary
        result = {}

        # --------- Data Processing ---------
        for index, header in enumerate(HEADERS):
            result[header] = gps_data[index]

        return result


def convert_OBD_data(obd_data):
    """
    Function that'll convert Raw OBD data to Readable JSON Object
    """

    # --------- Headers for final dictionary ---------
    HEADERS = ['Live/Memory', 'Signature', 'IMEI', 'Message Type', 'Sequence No', 'Time (GMT)', 'Date', 'OBD Protocol']

    # Result dictionary
    result = {}

    # --------- Data processing ---------
    first_half_raw = obd_data[:8]
    second_half_raw = obd_data[8:-1]

    # --------- First Half Data Processing ---------
    for index, header in enumerate(HEADERS):
        result[header] = first_half_raw[index]

    # --------- Second Half Data Processing ---------
    for pid in second_half_raw:
        i = pid.split(':')
        if len(i) > 1:
            result[i[0]] = i[1]

    return result


def convert_raw_to_information(input_data):
    """
    Function that'll convert Raw input from OBD to formatted dictionary containing all the information
    needed for the UI
    """
    # --------- Data decoding from byte to str ---------
    input_file = input_data.decode("UTF-8", errors='ignore')

    # --------- Data splitting based on comma ---------
    input_file = input_file.replace(';', ',')
    raw_data = input_file.split(',')

    # --------- Check for Login packet ---------
    if len(raw_data) < 8:
        login_data = convert_LOGIN_data(raw_data)
    
        return login_data

    # --------- GPS vs OBD Data ---------
    elif raw_data[1] == "ATL":
        gps_data = convert_GPS_data(raw_data)

        return gps_data

    elif raw_data[1] == "ATLOBD":
        obd_data = convert_OBD_data(raw_data)
        rpm = calculate_engine_RPM(obd_data)
        print(f'Engine RPM = {rpm}')
        return obd_data
    # -----------------------------------


if __name__ == '__main__':
    #AWS IP
    HOST = '172.31.81.140'  # Standard loopback interface address (localhost)
    PORT = 21212  # Port to listen on (non-privileged ports are > 1023)

    gpslist_lat=[]
    gpslist_lon=[]

    data = b'L,ATLOBD,866039048578802,03,4235,114809,140721,CAN,0101:0007E100,0103:0200,0104:65,0105:88,010A:XX,010B:1C,010C:168C,010D:0E,010E:A0,010F:67,0110:XXXX,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0902:4D414A4158584D524B4148443236383531000000,$ATLOBD,*A'
    print("TimeStamp: ", datetime.datetime.now())
    print(data)

    if convert_raw_to_information(data)["Message Type"] == "02" and convert_raw_to_information(data)["Live/Memory"] == "L":
        lat = convert_raw_to_information(data)["Latitude"]
        lon = convert_raw_to_information(data)["Longitude"]
        if count == 0:
            gpslist_lat.insert(0,lat)
            gpslist_lon.insert(0,lon)
            if lat == "":
                print("No Lat Lon available")
            else:
                count += 1
                coordinates = {'Latitude' : lat, 'Longitude' : lon }
                gps_one(lat, lon)
        else:
            
            coordinates = {'Latitude' : lat, 'Longitude' : lon }
            gps_main(gpslist_lat[0],gpslist_lon[0],lat,lon)

        print("initial:",gpslist_lat[0],gpslist_lon[0])
        print("live: ",lat,lon)
    print("--------------------------------------------------------------------------------------------")
