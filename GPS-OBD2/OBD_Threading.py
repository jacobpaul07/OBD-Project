import boto3
import socket
import datetime
from obd_gps import gps_one, gps_main
from Utils.calculate_engine_RPM import calculate_engine_RPM
import threading
import pytz    


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


def new_client(deviceid , connection , address):
    print('In Threading : ', deviceid)
    count = 0
    gpslist_lat=[]
    gpslist_lon=[]

    print('Connected by', address)
    data = connection.recv(1024)
    print("TimeStamp: ", dateTimeIND)
    print(data)

    if not data:
        return

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
                    Key='{0}/GPS/Initial/OBD2--{1}.txt'.format(fData["IMEI"],str(dateTimeIND)))
                gps_one(lat, lon)
        else:     
            coordinates = {'Latitude' : lat, 'Longitude' : lon }
            cli.put_object(
                Body=str(coordinates),
                Bucket='ec2-obd2-bucket',
                Key='{0}/GPS/Live/OBD2--{1}.txt'.format(fData["IMEI"],str(dateTimeIND)))
            gps_main(gpslist_lat[0],gpslist_lon[0],lat,lon)

        print("initial:",gpslist_lat[0],gpslist_lon[0])
        print("live: ",lat,lon)
    connection.send(bytesPacket)
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
    IST = pytz.timezone('Asia/Kolkata') 
    dateTimeIND = datetime.datetime.now(IST).strftime("%Y-%m-%d%H:%M:%S.%f")
    devices = 0
    while True:
        devices = devices + 1
        print('On while waiting next OBD device: ', devices)
        conn, addr = obdSocket.accept()
        print("Conneting..",addr)
        
        # Initializing Threading
        thread = threading.Thread(
            target=new_client,
            args=(devices, conn, addr)
        )

        # Starting the Thread
        thread.start()
    obdSocket.close()

