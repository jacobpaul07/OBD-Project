#!/usr/bin/env python3
import socket
import datetime
import json

HOST = 'xxx.xxx.xxx.xxx'  # Standard loopback interface address (localhost)
PORT = 1000        # Port to listen on (non-privileged ports are > 1023)

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
                a = data.decode("utf-8")
                list =a.split(",")
                print(list)
                if not data:
                    break
                a = b'@866039048589957,00,1234,*CS'
                conn.send(b'@866039048589957,00,7318,*CS')
                print("--------------------------------------------------------------------------------------------------------")