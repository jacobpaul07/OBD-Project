import boto3
import socket
import datetime
from obd_gps import gps_one, gps_main


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
    # print("[UTF-8 Converted Data] \n {}".format(input_file))

    # --------- Data splitting based on comma ---------
    input_file = input_file.replace(';', ',')
    raw_data = input_file.split(',')
    # print("[UTF-8 Raw Data List] \n {}".format(raw_data))

    # --------- Check for Login packet ---------
    if len(raw_data) < 8:
        print("[LOGIN PACKET]: ", raw_data)
        login_data = convert_LOGIN_data(raw_data)
        cli.put_object(
            Body=str(login_data),
            Bucket='ec2-obd2-bucket',
            Key='Login/OBD2--{}.txt'.format(str(datetime.datetime.now())))
        return login_data

    # --------- GPS vs OBD Data ---------
    elif raw_data[1] == "ATL":
        print("[GPS PACKET]: ", raw_data)
        gps_data = convert_GPS_data(raw_data)
        if raw_data[0] == "L":
            cli.put_object(
                Body=str(gps_data),
                Bucket='ec2-obd2-bucket',
                Key='GPS/L/OBD2--{}.txt'.format(str(datetime.datetime.now())))

        elif raw_data[0] == "H":
            cli.put_object(
                Body=str(gps_data),
                Bucket='ec2-obd2-bucket',
                Key='GPS/H/OBD2--{}.txt'.format(str(datetime.datetime.now())))
        return gps_data

    elif raw_data[1] == "ATLOBD":
        print("[OBD PACKET]: ", raw_data)
        obd_data = convert_OBD_data(raw_data)
        cli.put_object(
            Body=str(obd_data),
            Bucket='ec2-obd2-bucket',
            Key='OBD/OBD2--{}.txt'.format(str(datetime.datetime.now())))
        return obd_data
    # -----------------------------------


if __name__ == '__main__':

    HOST = '192.168.29.30'  # Standard loopback interface address (localhost)
    PORT = 21212  # Port to listen on (non-privileged ports are > 1023)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Server is Listening...")
        print("Please Wait")
        count = 0
        gpslist_lat=[]
        gpslist_lon=[]
        while True:
            conn, addr = s.accept()
            print("Conneting..")

            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    print("TimeStamp: ", datetime.datetime.now())
                    print(data)
                    if not data:
                        break
                    cli = boto3.client('s3')
                    if convert_raw_to_information(data)["Message Type"] == "02" and convert_raw_to_information(data)["Live/Memory"] == "L":
                        lat = convert_raw_to_information(data)["Latitude"]
                        lon = convert_raw_to_information(data)["Longitude"]
                        if count == 0:
                            gpslist_lat.insert(0,lat)
                            gpslist_lon.insert(0,lon)
                            if lat == "":
                                print("No Lat Lon available")
                            else:
                                gps_one(lat, lon)
                                count += 1
                                coordinates = {'Latitude' : lat, 'Longitude' : lon }
                                  
                                cli.put_object(
                                    Body=str(coordinates),
                                    Bucket='ec2-obd2-bucket',
                                    Key='GPS/Initial/OBD2--{}.txt'.format(str(datetime.datetime.now())))
                        else:
                            gps_main(gpslist_lat[0],gpslist_lon[0],lat,lon)
                            coordinates = {'Latitude' : lat, 'Longitude' : lon }
                            cli.put_object(
                                Body=str(coordinates),
                                Bucket='ec2-obd2-bucket',
                                Key='GPS/Live/OBD2--{}.txt'.format(str(datetime.datetime.now())))

                        print("initial:",gpslist_lat[0],gpslist_lon[0])
                        print("live: ",lat,lon)

                    a = b'@866039048589957,00,1234,*CS'
                    conn.send(b'@866039048589171,00,0518,*CS')
                    print("--------------------------------------------------------------------------------------------")
