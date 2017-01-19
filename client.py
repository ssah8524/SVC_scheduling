#!/usr/bin/python           # This is client.py file

import socket,sys,time

s = socket.socket()
#host = socket.gethostname()
host = sys.argv[1]
port = int(sys.argv[2])

s.connect((host, port))

layerNo = 2
round = [-1,-1]
channelTraj = []
while True:

    message = ''
    while len(message) < 9:
        message = message + s.recv(1)

    if message == "finished!":
        break
    size = int(message.split(" ")[0])
    layer = int(message.split(" ")[1])

    name = ''
    while len(name) < 13:
        name = name +  s.recv(1)

    segmentNo = 10*int(name[7]) + int(name[8])
    if segmentNo == 0:
        round[layer] += 1

    if segmentNo + round[layer]*30 < 10:
        segString = '0' + str(segmentNo + round[layer]*30)
    else:
        segString = str(segmentNo + round[layer]*30)

    name = 'layer' + str(layer) + '_' + segString + '.svc'
    file = open('user_files/' + str(name),'wb')
    dat = ''
    start = time.time()
    while len(dat) < size:
        if size - len(dat) > 100000:
            dat = dat + s.recv(100000)
        elif size - len(dat) > 1000:
            dat = dat + s.recv(1000)
        elif size - len(dat) > 100:
            dat = dat + s.recv(100)
        else:
            dat = dat + s.recv(1)
    stop = time.time()
    recRate = (8 * sys.getsizeof(dat))/(stop - start))/1000000
    channelTraj.append(recRate)
    print recRate
    #while size(recRate) < 7:
    #        recRate = '0' + recRate
    #    s.send(recRate)

    file.write(dat)
    file.close()
channel = open('channel.csv','w')
channel.write(channelTraj)
channel.close()
s.close()
