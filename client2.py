#!/usr/bin/python           # This is client.py file

import socket

s = socket.socket()
host = socket.gethostname()
port = 10002

s.connect((host, port))

layerNo = 2
buffer = [-1 for i in range(layerNo)]

while True:

    message = s.recv(8)
    if message == "finished":
        break
    size = int(message.split(" ")[0])
    layer = int(message.split(" ")[1])
    buffer[layer] += 1

    stringLength = 12 if buffer[layer] < 10 else 13
    name = s.recv(stringLength)
    file = open('user2_files/' + name,'w')
    dat = s.recv(size)
    file.write(dat)
    file.close()
s.close()
