from socketThreading import SocketThread
import socket

LOCALHOST = "172.31.81.140"
PORT = 21212
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((LOCALHOST, PORT))
print("Server started")
print("Waiting for Device..")
while True:
    
    server.listen()
    clientsock, clientAddress = server.accept()
    newthread = SocketThread(clientAddress, clientsock)
    newthread.start()