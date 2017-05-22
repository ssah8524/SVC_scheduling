#!/usr/bin/python           # This is client.py file

import socket,sys,time

s = socket.socket()
#host = socket.gethostname()
host = sys.argv[1]
port = int(sys.argv[2])

s.connect((host, port))

layerNo = 3
round = [-1,-1,-1]
channelTraj = []
recRate = '0'
while True:

    message = ''
    while len(message) < 9:
        message = message + s.recv(1)

    if message == "finished!":
        break
    elif message == "sfinished":
        while len(recRate) < 5:
            recRate = '0' + recRate
        s.sendall(recRate[:5])
        continue

    size = int(message.split(" ")[0])
    #print size
    layer = int(message.split(" ")[1])

    name = ''
    while len(name) < 13:
        name = name +  s.recv(1)

    segmentNo = 10 * int(name[7]) + int(name[8])
    if segmentNo == 0:
        round[layer] += 1

    if segmentNo + round[layer] * 20 < 10:
        segString = '0' + str(segmentNo + round[layer] * 20)
    else:
        segString = str(segmentNo + round[layer] * 20)

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
    recRate = int((8 * sys.getsizeof(dat))/(stop - start)/1000000) #received rate in Mbps
    print recRate
    channelTraj.append(recRate)
    recRate = str(recRate)

    file.write(dat)
    file.close()
channel = open('channel.csv','w')
channel.write(str(channelTraj))
channel.close()
s.close()
