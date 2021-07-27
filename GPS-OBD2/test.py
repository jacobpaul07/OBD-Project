import boto3
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
        IMEI = login_data["IMEI"]
        cli.put_object(
            Body=str(login_data),
            Bucket='ec2-obd2-bucket',
            Key='{0}/Login/OBD2--{1}.txt'.format(IMEI,str(datetime.datetime.now())))
        return login_data

    # --------- GPS vs OBD Data ---------
    elif raw_data[1] == "ATL":
        gps_data = convert_GPS_data(raw_data)
        IMEI = gps_data["IMEI"]
        if raw_data[0] == "L":
            cli.put_object(
                Body=str(gps_data),
                Bucket='ec2-obd2-bucket',
                Key='{0}/GPS/L/OBD2--{1}.txt'.format(IMEI,str(datetime.datetime.now())))

        elif raw_data[0] == "H":
            cli.put_object(
                Body=str(gps_data),
                Bucket='ec2-obd2-bucket',
                Key='{0}/GPS/H/OBD2--{1}.txt'.format(IMEI,str(datetime.datetime.now())))
        return gps_data

    elif raw_data[1] == "ATLOBD":
        obd_data = convert_OBD_data(raw_data)
        rpm = calculate_engine_RPM(obd_data)
        print(f'Engine RPM = {rpm}')
        IMEI = obd_data["IMEI"]
        cli.put_object(
            Body=str(obd_data),
            Bucket='ec2-obd2-bucket',
            Key='{0}/OBD/OBD2--{1}.txt'.format(IMEI,str(datetime.datetime.now())))
        return obd_data
    # -----------------------------------


if __name__ == '__main__':
    #AWS IP
    HOST = '172.31.81.140'  # Standard loopback interface address (localhost)
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
            print(s.accept())
            print("Conneting..")

            with conn:
                print('Connected by', addr)
                data = conn.recv(1024)
                print("TimeStamp: ", datetime.datetime.now())
                print(data)

                if not data:
                    break
                cli = boto3.client('s3')
                fData = convert_raw_to_information(data)

                IMEI = "@"+fData["IMEI"]
                messageType = "00"
                sequenceNumber = fData["Sequence No"]
                checkSum = "*CS"
                packet = IMEI,messageType,sequenceNumber,checkSum
                seperator = ","
                joinedPacket = seperator.join(packet)
                bytesPacket = bytes(joinedPacket, 'utf-8')
                print("Return Packet:",bytesPacket)

                if fData["Message Type"] == "02" and fData["Live/Memory"] == "L":
                    lat = fData["Latitude"]
                    lon = fData["Longitude"]
                    if count == 0:
                        gpslist_lat.insert(0,lat)
                        gpslist_lon.insert(0,lon)
                        if lat == "":
                            print("No Lat Lon available")
                        else:
                            count += 1
                            coordinates = {'Latitude' : lat, 'Longitude' : lon }
                                
                            cli.put_object(
                                Body=str(coordinates),
                                Bucket='ec2-obd2-bucket',
                                Key='{0}/GPS/Initial/OBD2--{1}.txt'.format(fData["IMEI"],str(datetime.datetime.now())))
                            gps_one(lat, lon)
                    else:
                        
                        coordinates = {'Latitude' : lat, 'Longitude' : lon }
                        cli.put_object(
                            Body=str(coordinates),
                            Bucket='ec2-obd2-bucket',
                            Key='{0}/GPS/Live/OBD2--{1}.txt'.format(fData["IMEI"],str(datetime.datetime.now())))
                        gps_main(gpslist_lat[0],gpslist_lon[0],lat,lon)

                    print("initial:",gpslist_lat[0],gpslist_lon[0])
                    print("live: ",lat,lon)

                # Harish OBD: IMEI = 866039048589957
                # Mani OBD : IMEI = 866039048589171
                # Aneesh OBD : IMEI = 866039048578802
                testbyte = b'@866039048589957,00,0707,*CS'
                conn.send(bytesPacket)
                # conn.send(testbyte)
                
                print("--------------------------------------------------------------------------------------------")

# if __name__ == '__main__':

#     print("Server is Listening...")
#     print("Please Wait")
#     count = 0
#     gpslist_lat = []
#     gpslist_lon = []

#     data = b'L,ATL,866039048589957,01,9231,*,'
#     print("TimeStamp: ", datetime.datetime.now())
#     print(data)
#     fData = convert_raw_to_information(data)

#     if fData["Message Type"] == "02" and fData["Live/Memory"] == "L":
#         lat = fData["Latitude"]
#         lon = fData["Longitude"]
#         print("Test",lat,lon)
#         if count == 0:
#             gpslist_lat.insert(0, lat)
#             gpslist_lon.insert(0, lon)
#             if lat == "":
#                 print("No Lat Lon available")
#             else:
#                 gps_one(lat, lon)
#                 count += 1
#         else:
#             gps_main(gpslist_lat[0], gpslist_lon[0], lat, lon)

#         print(count)
#         print("initial:", gpslist_lat[0], gpslist_lon[0])
#         print("live: ", lat, lon)

#     IMEI = "@"+fData["IMEI"]
#     messageType = "00"
#     sequenceNumber = fData["Sequence No"]
#     checkSum = "*CS"
#     packet = IMEI,messageType,sequenceNumber,checkSum
#     seperator = ","
#     joinedPacket = seperator.join(packet)
#     bytesPacket = bytes(joinedPacket, 'utf-8')
#     print(bytesPacket)

#     # conn.send(b'@866039048589171,00,0518,*CS')
#     print("------------------------------------------------------------------------------------------")

