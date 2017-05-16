## This file assumes a single class of users with a diagonal quality adaptation method with a pre-fetch threshold of 5 segments.

import time, threading, random, socket, numpy, sys

#argv = script name, slot duration, total simulation time, scheduling method
#channelMatrix = [0.9,0.1,0,0,0.1,0.8,0.1,0,0,0.1,0.8,0.1,0,0,0.1,0.9]

def find_minmax(a, func):
    return [i for (i, val) in enumerate(a) if func(val)]

# Currently works for only two layers -- no buffer priority
def tie_breaker(users,ind,remain):
    output = [0 for x in range(remain)]
    for i in range(remain):
        k = random.randint(0,len(ind)-1)
        output[i] = ind[k]
        ind.pop(k)
    return output

class statistics:
    def __init__(self,parameters):
        self.receiverBuffer = [0 for i in range(parameters.numLayer)]
        self.rebuf = 0
        self.chanStateTraj = []
        self.rebuffSlots = []
    def layerRatio(self): #For now this works for two layers only
        if float(self.receiverBuffer[0] + self.receiverBuffer[1]) != 0:
            return float(self.receiverBuffer[0])/float(self.receiverBuffer[0] + self.receiverBuffer[1])
        else:
            return 0
    def averageRate(self):
        return numpy.mean(self.chanStateTraj)
    def writeFiles(self,userIndex):
        outputReward = open('reward_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputRebuf = open('rebuf_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputChanTraj = open('trajectory_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputLayerRatio = open('layer_ratio_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputRebufSlots = open('rebuf_slots_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        #outputReward.write(str(self.finalReward))
        outputRebuf.write(str(self.rebuf))
        outputRebufSlots.write(str(self.rebuffSlots))

        temp = self.chanStateTraj
        if self.chanStateTraj[0] == '[':
            temp.pop(0)     
        if self.chanStateTraj[len(self.chanStateTraj) - 1] == ']':
            temp.pop(len(temp) - 1)
        outputChanTraj.write(str(temp))
        outputLayerRatio.write(str(self.receiverBuffer[0]) + ',' + str(self.receiverBuffer[1]))
        outputReward.close()
        outputRebuf.close()
        outputChanTraj.close()
        outputLayerRatio.close()
        outputRebufSlots.close()

class param:
    def __init__(self):
        self.userNum = int(sys.argv[1])
        self.preFetchThreshold = int(sys.argv[2])
        self.timeSlot = float(sys.argv[3]) #duration of one scheduling slot
        self.totSimTime = int(sys.argv[4]) #duration of the entire simulation
        self.bufferLimit = 20
        self.chanStates = 4
        self.numLayer = 2
        self.discount = 0.99
        self.epsilon = 0.01

class user:
    def __init__(self,parameters):
        # For now let's assume that all users start from an initially empty buffer
        self.param = parameters
        self.buffer = [0 for i in range(parameters.numLayer)]
        self.oldBuffer = [0 for i in range(parameters.numLayer)]
        self.nextToBeSent = [0 for l in range(parameters.numLayer)]
        self.chan = 0
        self.tc = 100
        self.rateAccum = 0.0
        self.bufTracker = 0.0
        self.receivedSegments = [0 for i in range(parameters.numLayer)]
        self.stats = statistics(parameters)
    def reward():
        return 0


class scheduler:
    def __init__(self,mode,parameters):
        self.param = parameters
        self.users = [user(parameters) for i in range(parameters.userNum)]
        self.mode = mode
    def schedule(self):
        active_v = -1

        if self.mode == 'maxrate':
            cur_rates = [0 for x in range(self.param.userNum)]
            for u in range(self.param.userNum):
                cur_rates[u] = self.users[u].chan
            candidate = find_minmax(cur_rates, lambda x: x == max(cur_rates))
            if len(candidate) > 1: #randomly choose between them
                k = random.randint(0,len(candidate)-1)
                active_v = candidate[k]
            else:
                active_v = candidate[0]
        elif self.mode == 'pf':
            propRates = [0.0 for x in range(self.param.userNum)]
            for u in range(self.param.userNum):
                if self.users[u].rateAccum == 0:
                    denom = 0.01
                else:
                    denom = self.users[u].rateAccum
                propRates[u] = self.users[u].chan / denom
            candidate = find_minmax(propRates, lambda x: x == max(propRates))
            if len(candidate) > 1: #randomly choose between them
                k = random.randint(0,len(candidate)-1)
                active_v = candidate[k]
            else:
                active_v = candidate[0]
        elif self.mode == 'heuristic':
            chanCandidate = [u for u in range(self.param.userNum) if self.users[u].chan == max([self.users[i].chan for i in range(self.param.userNum) if self.users[i].bufTracker <= 0])]
            if len(chanCandidate) == 0:
                bufCandidate = [u for u in range(self.param.userNum) if self.users[u].buffer[0] == min([self.users[i].buffer[0] for i in range(self.param.userNum) if self.users[i].bufTracker > 0])]
                if len(bufCandidate > 1):
                    k = random.randint(0,len(bufCandidate)-1)
                    active_v = bufCandidate[k]
                else:
                    active_v = bufCandidate[0]
            elif len(chanCandidate) > 1:
                k = random.randint(0,len(chanCandidate)-1)
                active_v = chanCandidate[k]
            else:
                active_v = chanCandidate[0]
        elif self.mode == 'maxurgency':
            curBase = [self.users[u].buffer[0] for u in range(self.param.userNum)]
            candidate = find_minmax(curBase, lambda x: x == min(curBase))
            if len(candidate) > 1: #randomly choose between them
                k = random.randint(0,len(candidate)-1)
                active_v = candidate[k]
            else:
                active_v = candidate[0]

        for i in range(self.param.userNum):
            if active_v == i:
                self.users[i].rateAccum = (1 - 1.0/self.users[i].tc)*self.users[i].rateAccum + (1.0/self.users[i].tc)*self.users[i].chan
                self.users[i].bufTracker += self.param.epsilon * ((self.users[i].buffer[0] - self.users[i].oldBuffer[0]) + self.users[i].buffer[1] - self.users[i].oldBuffer[1])
            else:
                self.users[i].rateAccum = (1 - 1.0/self.users[i].tc)*self.users[i].rateAccum
                self.users[i].bufTracker -= self.param.epsilon
        return active_v

    def NextSegmentsToSend(self,activeUser):
        sendBuffer = [[0 for u in range(self.param.numLayer)] for u in range(self.param.userNum)]
        sendBuffer[activeUser][0] == 1
        for u in range(self.param.userNum):
            self.users[u].oldBuffer = [self.users[u].buffer[l] for l in range(self.param.numLayer)]
        return sendBuffer

    def transmit(self,queue,sockets,activeVector):
        breakUser = False
        breakLayer = False
        startTime = time.time()
        for i in range(self.param.userNum):
            if activeVector == i:
                for l in range(self.param.numLayer):
                    if queue[i][l] % 20 < 10:
                        segString = '0' + str(queue[i][l] % 20)
                    else:
                        segString = str(queue[i][l] % 20)
                    fileName = 'layer' + str(l) + '_' + segString + '.svc'
                    sockets.transmitFile(fileName,i)
                    self.users[i].buffer[l] += 1
                    self.users[i].stats.receiverBuffer[l] += 1
                    self.users[i].nextToBeSent[l] = queue[i][l] + 1
            sockets.cliSockets[i].sendall("sfinished")
            txRate = float(sockets.cliSockets[i].recv(5))
            self.users[i].chan = txRate
            self.users[i].stats.chanStateTraj.append(self.users[i].chan)

        if time.time() - startTime < self.param.timeSlot:
            time.sleep(self.param.timeSlot - time.time() + startTime)

class fileBuffer:
    def __init__(self,parameters):
        self.buffer = [[] for l in range(parameters.numLayer)]
    def sortRequestedSegments(self):
        for l in range(Parameters.numLayer):
            if self.buffer[l] != []:
                self.buffer[l] = sorted(self.buffer[l])

class socketHandler:
    def __init__(self,Parameters):
        self.param = Parameters
        self.portNo = [int(sys.argv[6]) + i for i in range(Parameters.userNum)]
        self.servSockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for i in range(Parameters.userNum)]
        self.cliSockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for i in range(Parameters.userNum)]
        self.host = socket.gethostname()
        #self.host = "192.168.0.100"
    def establishConnection(self): #Waits until all users have tuned in
        for i in range(self.param.userNum):
            self.servSockets[i].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.servSockets[i].bind((self.host,self.portNo[i]))
            self.servSockets[i].listen(5)
            self.cliSockets[i] = self.servSockets[i].accept()[0]

    def closeConnection(self):
        for i in range(self.param.userNum):
            self.servSockets[i].close
    def transmitFile(self,fileName,receivingUser):
        f = open('service_files/' + fileName,'rb')
        File = f.read()
        fileSize = str(len(File))
        while len(fileSize) < 7: # Assuming the longest file size has 7 digits.
            fileSize = '0' + fileSize
        layer = fileName[5]
        
        self.cliSockets[receivingUser].sendall(fileSize + " " + str(layer))
        self.cliSockets[receivingUser].sendall(fileName)
        self.cliSockets[receivingUser].sendall(str(File))

### Main program starts here! ###

Parameters = param()
#Parameters.createVectors()
BSNode = scheduler(sys.argv[5],Parameters)
Sockets = socketHandler(Parameters)

Sockets.establishConnection()

totalTime = 0
stateTracker = [0 for i in range(Parameters.userNum)]
ticker = 0

while True:

#for i in range(Parameters.userNum):
#print BSNode.users[i].chan

    if totalTime > ticker * 10:
        print 'elapsed time: ' + str(totalTime)
        ticker += 1

    start = time.time()
    scheduledUsers = BSNode.schedule()

### Reward function must come here

##################################

#    for u in range(Parameters.userNum):
#        print BSNode.users[u].buffer,BSNode.users[u].oldBuffer

    sendingQueue = BSNode.NextSegmentsToSend(scheduledUsers)

    BSNode.transmit(sendingQueue,Sockets,scheduledUsers)

#for u in range(Parameters.userNum):
#        print BSNode.users[u].buffer,BSNode.users[u].oldBuffer
#    print '=============================='

    end = time.time()
    totalTime += end - start

    if totalTime >= Parameters.totSimTime:
        break
for i in range(Parameters.userNum):
    Sockets.cliSockets[i].send("finished!")
Sockets.closeConnection()

meanLayerRatio = numpy.mean([BSNode.users[u].stats.layerRatio() for u in range(Parameters.userNum)])
meanChannel = numpy.mean([BSNode.users[u].stats.averageRate() for u in range(Parameters.userNum)])
meanRebuf = numpy.mean([BSNode.users[u].stats.rebuf for u in range(Parameters.userNum)])

print meanRebuf, meanRebuf/totalTime

for i in range(Parameters.userNum):
    BSNode.users[i].stats.writeFiles(i+1)

