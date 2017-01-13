#!/usr/bin/python           # This is client.py file

import socket

s = socket.socket()
host = socket.gethostname()
port = 10002

s.connect((host, port))

layerNo = 2
buffer = [-1 for i in range(layerNo)]

while True:

    message = s.recv(9)
    if message == "finished!":
        break
    size = int(message.split(" ")[0])
    layer = int(message.split(" ")[1])
    buffer[layer] += 1

    stringLength = 12 if buffer[layer] < 10 else 13
    name = s.recv(stringLength)
    file = open(r'user2_files/' + str(name),'wb')
    dat = ''
    while len(dat) < size:
        if size - len(dat) > 100000:
            dat = dat + s.recv(100000)
        elif size - len(dat) > 1000:
            dat = dat + s.recv(1000)
        elif size - len(dat) > 100:
            dat = dat + s.recv(100)
        else:
            dat = dat + s.recv(1)
    file.write(dat)
    file.close()
s.close()
