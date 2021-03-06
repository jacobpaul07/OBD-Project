import socket
import datetime


def convert_raw_to_information(input_file):
    """
    Function that'll convert Raw input from OBD to formatted dictionary containing all the information
    needed for the UI
    """

    # --------- Headers for final dictionary ---------
    HEADERS = ['Live/Memory', 'Signature', 'IMEI', 'Message Type', 'Sequence No', 'Time (GMT)', 'Date', 'OBD Protocol']

    # Result dictionary
    result = {}

    # --------- Data processing ---------
    raw_data = input_file.split(',')
    first_half_raw = raw_data[:8]
    second_half_raw = raw_data[8:-1]

    # --------- First Half Data Processing ---------
    for index, header in enumerate(HEADERS):
        result[header] = first_half_raw[index]

    # --------- Second Half Data Processing ---------
    for pid in second_half_raw:
        i = pid.split(':')
        if len(i) > 1:
            result[i[0]] = i[1]

    return result


if __name__ == '__main__':

    HOST = ''  # Standard loopback interface address (localhost)
    PORT = 1000  # Port to listen on (non-privileged ports are > 1023)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Server is Listening...")
        print("Please Wait")

        while True:
            conn, addr = s.accept()
            print("Conneting ..")

            with conn:
                print('Connected by', addr)
                while True:
                    data = conn.recv(1024)
                    print("TimeStamp: ", datetime.datetime.now())
                    print(data)
                    byte_data = data.decode("utf-8")
                    list = byte_data.split(",")
                    #print(list)
                    if not data:
                        break
                    # --------- This is the input to Server every minute ---------
                    # raw_data = 'L,ATLOBD,866795030623415,03,6816,073203,070419,CAN,0101:00076100,0103:0200,0104:69,0105:7F,010A:XX,010B:4D,010C:1977,010D:2F,010E:BC,010F:54,0110:XXXX,0111:2B,011C:06,011F:012D,0121:0000,0122:XXXX,012F:XX,0162:XX,0132:XXXX,0133:60,0143:006E,0145:13,0146:XX,0147:2E,0148:XX,0149:2F,014A:17,014B:XX,014C:1F,0151:XX,0131:9174,0144:XXXX,015E:XXXX,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0902:XXXXXXXXXXXXXXXXXXXX,$ATLOBD,*8'
                    byte_data = b'L,ATL,866039048589957,02,7510,070339,070621,A,17.488947;N,78.346046;E,0,251,19.84,4.2,15,404,49,4f34,6754,#0031,0,ATL,*k'
                    raw_data = byte_data.decode('UTF-8')

                    # --------- Call function here ---------
                    print("\t----- Result Output To Be Stored In Database -----")
                    information = convert_raw_to_information(raw_data)
                    print(information)

                    # Send response to OBD
                    a = b'@866039048589957,00,1234,*CS'
                    conn.send(b'@866039048589957,00,7318,*CS')
                    print(
                        "--------------------------------------------------------------------------------------------------------")


