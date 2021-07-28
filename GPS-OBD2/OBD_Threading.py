import boto3
import socket
import datetime
from obd_gps import gps_one, gps_main
from Utils.calculate_engine_RPM import calculate_engine_RPM
import threading
import pytz    

# Threading lock
global_lock = threading.Lock()

# Initializing The StopThread as boolean-False
stopThread: bool = False

listOfActiveDevices = []


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
    IST = pytz.timezone('Asia/Kolkata') 
    dateTimeIND = datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S.%f")
    # --------- Data decoding from byte to str ---------
    input_file = input_data.decode("UTF-8", errors='ignore')

    # --------- Data splitting based on comma ---------
    input_file = input_file.replace(';', ',')
    raw_data = input_file.split(',')

    # --------- Check for Login packet ---------
    if len(raw_data) < 8:
        login_data = convert_LOGIN_data(raw_data)
        IMEI = login_data["IMEI"]
        # S3 Log Login Data
        cli.put_object(
            Body=str(login_data),
            Bucket='ec2-obd2-bucket',
            Key='{0}/Login/Log/OBD2--{1}.txt'.format(IMEI,str(dateTimeIND)))
        
        # S3 Latest Login Data
        cli.put_object(
            Body=str(login_data),
            Bucket='ec2-obd2-bucket',
            Key='{0}/Login/Latest/login.txt'.format(IMEI))
        return login_data

    # --------- GPS Data ---------
    elif raw_data[1] == "ATL":
        gps_data = convert_GPS_data(raw_data)
        IMEI = gps_data["IMEI"]
        # S3 Log GPS Data
        cli.put_object(
            Body=str(gps_data),
            Bucket='ec2-obd2-bucket',
            Key='{0}/GPS/Log/OBD2--{1}.txt'.format(IMEI,str(dateTimeIND)))

        if raw_data[0] == "L":     
            # S3 Latest GPS 'L' Data
            cli.put_object(
                Body=str(gps_data),
                Bucket='ec2-obd2-bucket',
                Key='{0}/GPS/Latest/L.txt'.format(IMEI))
            
        elif raw_data[0] == "H":
             # S3 Latest GPS 'H' Data
            cli.put_object(
                Body=str(gps_data),
                Bucket='ec2-obd2-bucket',
                Key='{0}/GPS/Latest/H.txt'.format(IMEI))
        return gps_data

    # --------- OBD Data ---------
    elif raw_data[1] == "ATLOBD":
        obd_data = convert_OBD_data(raw_data)
        rpm = calculate_engine_RPM(obd_data)
        IMEI = obd_data["IMEI"]
        
        if rpm:
            print(f'Engine RPM = {rpm}')
            rpmdata = { 'RPM' : rpm, 'IMEI': IMEI,'timestamp' : dateTimeIND}  
            cli.put_object(
                Body=str(rpmdata),
                Bucket='ec2-obd2-bucket',
                Key='{0}/Data/{0}_rpm.txt'.format(IMEI))
        else:
            print("No RPM data received")
        
        # S3 RPM Data
        cli.put_object(
                Body=str(rpm),
                Bucket='ec2-obd2-bucket',
                Key='{0}/OBD/Latest/RPM.txt'.format(IMEI))
        # S3 Log OBD Data
        cli.put_object(
            Body=str(obd_data),
            Bucket='ec2-obd2-bucket',
            Key='{0}/OBD/Log/OBD2--{1}.txt'.format(IMEI,str(dateTimeIND)))

        if raw_data[0] == "L":     
            # S3 Latest OBD 'L' Data
            cli.put_object(
                Body=str(obd_data),
                Bucket='ec2-obd2-bucket',
                Key='{0}/OBD/Latest/L.txt'.format(IMEI))
            
        elif raw_data[0] == "H":
             # S3 Latest GPS 'H' Data
            cli.put_object(
                Body=str(obd_data),
                Bucket='ec2-obd2-bucket',
                Key='{0}/OBD/Latest/H.txt'.format(IMEI))

        return obd_data
    # -----------------------------------


def new_client(deviceid , connection , address):
    with global_lock:
        print('In Threading : Site', deviceid)
        count = 0
        gpslist_lat=[]
        gpslist_lon=[]

        IST = pytz.timezone('Asia/Kolkata') 
        dateTimeIND = datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S.%f")
        print('Connected by', address)
        try:
            data = connection.recv(1024)
            print("TimeStamp: ", dateTimeIND)
            print(data)

            if not data:
                return

            fData = convert_raw_to_information(data)
            IMEI = fData["IMEI"]
            atIMEI = "@"+IMEI
            messageType = "00"
            sequenceNumber = fData["Sequence No"]
            checkSum = "*CS"
            packet = atIMEI,messageType,sequenceNumber,checkSum
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
                        coordinates = {'Latitude' : lat, 'Longitude' : lon,'IMEI': IMEI, 'timestamp' : dateTimeIND}
                            
                        cli.put_object(
                            Body=str(coordinates),
                            Bucket='ec2-obd2-bucket',
                            Key='{0}/Data/{0}_lat_lon_initial.txt'.format(IMEI))
                        gps_one(lat, lon)
                else:     
                    coordinates = {'Latitude' : lat, 'Longitude' : lon, 'IMEI':IMEI, 'timestamp' : dateTimeIND }
                    cli.put_object(
                        Body=str(coordinates),
                        Bucket='ec2-obd2-bucket',
                        Key='{0}/Data/{0}_lat_lon.txt'.format(IMEI))
                    gps_main(gpslist_lat[0],gpslist_lon[0],lat,lon)

                print("initial:",gpslist_lat[0],gpslist_lon[0])
                print("live: ",lat,lon)
            connection.send(bytesPacket)

        except Exception as exception:
            print ("Error:",exception)
        print(count)
        print("--------------------------------------------------------------------------------------------")

        # Initializing Thread Callback
        thread = threading.Thread(
            target=new_client,
            args=(deviceid , connection, address)
        )
        # Starting the Thread
        thread.start()
        
    

if __name__ == '__main__':

    cli = boto3.client('s3')

    #AWS IP
    HOST = '172.31.81.140'  # Standard loopback interface address (localhost)s
    PORT = 21212  # Port to listen on (non-privileged ports are > 1023)

    obdSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    obdSocket.bind((HOST, PORT))
    obdSocket.listen()
    print("Server is Listening...")
    print("Please Wait")
    devices = 0
    while True:
        devices = devices + 1
        print('Waiting for next OBD device: ', devices)
        conn, addr = obdSocket.accept()
        print("Conneting to Device with IP:",addr)
        
        # Initializing Threading
        thread = threading.Thread(
            target=new_client,
            args=(devices, conn, addr)
        )

        print(str(thread.native_id))
        # Starting the Thread
        thread.start()

    obdSocket.close()

