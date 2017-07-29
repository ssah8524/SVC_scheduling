## This file assumes a single class of users with a diagonal quality adaptation method with a pre-fetch threshold of 5 segments.

import time, threading, random, socket, numpy, sys, math, subprocess

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
        self.totalReward = 0
        self.chanStateTraj = []
        self.rebuffSlots = []
    	
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
	if len(temp) > 0:	   
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
        self.playbackDelay = 0
        self.userNum = int(sys.argv[1])
        self.preFetchThreshold = int(sys.argv[2])
        self.timeSlot = float(sys.argv[3]) #duration of one scheduling slot
        self.totSimTime = int(sys.argv[4]) #duration of the entire simulation
        self.bufferLimit = 20
        self.chanStates = 4
        self.numLayer = 3
        self.frameRates = [6,12,24]
        self.discount = 0.99
        self.epsilon = 0.1
        self.Tseg = 1

class user:
    alpha = 2
    beta = 0.63
    penalty = -0.05
    def __init__(self,parameters):
        # For now let's assume that all users start from an initially empty buffer
        self.param = parameters
        self.buffer = [0 for i in range(parameters.numLayer)]
        self.oldBuffer = [0 for i in range(parameters.numLayer)]
        self.rate = 0.1
        self.tc = 100
        self.rateAccum = 0.0
        self.bufTracker = 0.0
        self.rebufFlag = 0
        self.plTime = 0.0
        self.IPLastByte = -1
        self.rssi = -100
        self.lastSegs = [-1 for u in range(parameters.numLayer)]
        self.stats = statistics(parameters)
    def reward(self,dlTime,subSeg):
	if time.time() - initialTime >= self.param.totSimTime:
	    return 
        numSegs = int((self.plTime + dlTime) / self.param.Tseg)
        residue = self.param.Tseg * ((self.plTime + dlTime) / self.param.Tseg - int((self.plTime + dlTime) / self.param.Tseg))
        r = 0

        #print self.buffer[0], self.buffer[1]
        for s in range(numSegs + 1):
            layers = 0
            dur = self.param.Tseg
            for l in range(self.param.numLayer):
                if self.buffer[l] > s:
                    layers += 1
                else:
                    break
            if s == 0:
                dur -= self.plTime
            elif residue > 0:
                dur = residue

            if layers > 0:
                r += ((1 - math.exp(-1 * self.alpha * (float(self.param.frameRates[layers - 1]) / float(self.param.frameRates[self.param.numLayer - 1]))**self.beta)) / (1 - math.exp(-1 * self.alpha))) * dur * self.param.discount**(time.time() - initialTime - self.param.playbackDelay)

            else: ##This occurs if we have re-buffering
                r += self.penalty * dur * self.param.discount**(time.time() - initialTime - self.param.playbackDelay)
                #r +=1.0/self.param.totSimTime *  self.penalty * dur
        self.stats.totalReward += r

class scheduler:
    def __init__(self,mode,parameters):
        self.param = parameters
        self.users = [user(parameters) for i in range(parameters.userNum)]
        self.mode = mode
        self.dlTime = 0.0
    def schedule(self):
        active_v = -1
        if self.mode == 'maxrate':
            cur_chan = [0 for x in range(self.param.userNum)]
            for u in range(self.param.userNum):
                cur_chan[u] = self.users[u].rssi
            candidate = find_minmax(cur_chan, lambda x: x == max(cur_chan))
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
                propRates[u] = self.users[u].rate / denom
            candidate = find_minmax(propRates, lambda x: x == max(propRates))
            if len(candidate) > 1: #randomly choose between them
                k = random.randint(0,len(candidate) - 1)
                active_v = candidate[k]
            else:
                active_v = candidate[0]
	    
	
        elif self.mode == 'heuristic':

	    tmpCan = [self.users[i].rssi for i in range(self.param.userNum) if self.users[i].bufTracker <= 0 and self.users[i].bufTracker == min([self.users[j].bufTracker for j in range(self.param.userNum)])]
	    #tmpCan = [self.users[i].rssi for i in range(self.param.userNum) if self.users[i].bufTracker <= 0]	
	    if len(tmpCan) > 0:
            	chanCandidate = [u for u in range(self.param.userNum) if self.users[u].rssi == max(tmpCan)]
	    else:
	        chanCandidate = []
	    
	    if len(chanCandidate) == 0:
                bufCandidate = [u for u in range(self.param.userNum) if self.users[u].buffer[0] == min([self.users[i].buffer[0] for i in range(self.param.userNum) if self.users[i].bufTracker > 0])]
                if len(bufCandidate) > 1:
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
                self.users[i].rateAccum = (1 - 1.0/self.users[i].tc) * self.users[i].rateAccum + (1.0/self.users[i].tc) * self.users[i].rate
		self.users[i].bufTracker = (1 - self.param.epsilon) * self.users[i].bufTracker + self.param.epsilon * ((self.users[i].buffer[0] - self.users[i].oldBuffer[0]) + (self.users[i].buffer[1] - self.users[i].oldBuffer[1]) + (self.users[i].buffer[2] - self.users[i].oldBuffer[2]) + 2)
            else:
                self.users[i].rateAccum = (1 - 1.0/self.users[i].tc) * self.users[i].rateAccum
                self.users[i].bufTracker -= self.dlTime * self.param.epsilon
#           	self.users[i].bufTracker = (1 - self.param.epsilon) * self.users[i].bufTracker + self.param.epsilon * ((self.users[i].buffer[0] - self.users[i].oldBuffer[0]) + (self.users[i].buffer[1] - self.users[i].oldBuffer[1]) + (self.users[i].buffer[2] - self.users[i].oldBuffer[2]))      
#	print [self.users[i].bufTracker for i in range(self.param.userNum)]
#	print active_v
        return active_v

    def NextSegmentsToSend(self,activeUser):

        for u in range(self.param.userNum):
            self.users[u].oldBuffer = [self.users[u].buffer[l] for l in range(self.param.numLayer)]

        layerToRequest = 0
	flag = 0
        segmentToRequest = -1
	diff = [0 for i in range(self.param.numLayer)]
        for l in range(self.param.numLayer - 1):
	    diff[l] = self.users[activeUser].buffer[l] - self.users[activeUser].buffer[l + 1]
            if diff[l] < self.param.preFetchThreshold and self.users[activeUser].buffer[l] < self.param.bufferLimit:
		layerToRequest = l
		flag = 1
		break
	    elif self.users[activeUser].buffer[l] == self.param.bufferLimit:
		diff[l] = -1000
	if flag == 0:
	    Request = find_minmax(diff,lambda x: x == max(diff))
	    layerToRequest = Request[0]
	##Temporary manual trick
        if diff[0] == self.param.preFetchThreshold and diff[1] > 0:
	    layerToRequest = 2        

        if layerToRequest == 0: ##If base layer is requested, it should be consecutive because no jumps are allowed in the base layer.
            segmentToRequest = self.users[activeUser].lastSegs[0] + 1
        else:
            segmentToRequest = max(math.ceil((time.time() - initialTime - self.param.playbackDelay - self.users[activeUser].stats.rebuf) / self.param.Tseg),self.users[activeUser].lastSegs[layerToRequest] + 1)
        return [segmentToRequest,layerToRequest]

    def transmit(self,subSeg,sockets,activeUser):
        startTime = time.time()
        if subSeg[0] % 20 < 10:
            segString = '0' + str(int(subSeg[0] % 20))
        else:
            segString = str(int(subSeg[0] % 20))
        fileName = 'layer' + str(subSeg[1]) + '_' + segString + '.svc'
        sockets.transmitFile(fileName,activeUser)
        sockets.cliSockets[activeUser].sendall("sfinished")
        txRate = float(sockets.cliSockets[activeUser].recv(5))
        self.users[activeUser].rate = txRate
        self.users[activeUser].stats.chanStateTraj.append(self.users[activeUser].rssi)

        self.dlTime = time.time() - startTime
        #print '++++'
        if time.time() - initialTime > self.param.playbackDelay:
            for u in range(self.param.userNum):
	#	print self.users[u].buffer,activeUser,self.users[u].plTime,self.dlTime,subSeg[1]
                if self.param.Tseg * self.users[u].buffer[0] - self.users[u].plTime < self.dlTime:
                    self.users[u].stats.rebuf += self.dlTime - self.param.Tseg * self.users[u].buffer[0] + self.users[u].plTime
                    self.users[u].rebufFlag = 1
            	self.users[u].reward(self.dlTime,subSeg)  ## The reward is calculated here.
        if subSeg[1] == 0:
            self.users[activeUser].lastSegs[0] += 1
            self.users[activeUser].buffer[0] = min(self.param.bufferLimit,self.users[activeUser].buffer[0] + 1)
            self.users[activeUser].stats.receiverBuffer[0] = min(self.param.totSimTime,self.users[activeUser].stats.receiverBuffer[0] + 1)
        else:
            self.users[activeUser].lastSegs[subSeg[1]] += 1
            if self.param.Tseg * subSeg[0] + self.param.playbackDelay - self.users[activeUser].plTime >= self.dlTime:
                self.users[activeUser].buffer[subSeg[1]] = min(self.param.bufferLimit,self.users[activeUser].buffer[subSeg[1]] + 1)
		if self.users[activeUser].buffer[subSeg[1]] + 1 <= self.param.bufferLimit:
                    self.users[activeUser].stats.receiverBuffer[subSeg[1]] = min(self.param.totSimTime,self.users[activeUser].stats.receiverBuffer[subSeg[1]] + 1)
        for u in range(self.param.userNum):
            for l in range(self.param.numLayer):
                self.users[u].buffer[l] = max(0,self.users[u].buffer[l] - math.floor(self.users[u].plTime + self.dlTime))
            self.users[u].plTime  = (self.users[u].plTime + self.dlTime) - math.floor(self.users[u].plTime + self.dlTime)
            if self.users[u].rebufFlag == 1:
                self.users[u].plTime = 0
                self.users[u].rebufFlag = 0

class socketHandler:
    def __init__(self,Parameters):
        self.param = Parameters
        self.portNo = [int(sys.argv[6]) + i for i in range(Parameters.userNum)]
        self.servSockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for i in range(Parameters.userNum)]
        self.cliSockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for i in range(Parameters.userNum)]
        #self.host = socket.gethostname()
        self.host = "192.168.0.100"
    def establishConnection(self): #Waits until all users have tuned in
	addresses = [0 for i in range(self.param.userNum)]
        for i in range(self.param.userNum):
            self.servSockets[i].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.servSockets[i].bind((self.host,self.portNo[i]))
            self.servSockets[i].listen(5)
            acceptArg = self.servSockets[i].accept()
            self.cliSockets[i] = acceptArg[0]
            addresses[i] = acceptArg[1]
        return addresses
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

##First, the AP pings all users to add the entry into the ARP table.
Parameters = param()

BSNode = scheduler(sys.argv[5],Parameters)
Sockets = socketHandler(Parameters)
addresses = Sockets.establishConnection()
for i in range(Parameters.userNum):
    if str(addresses[i])[13] == "'":
        IP = str(addresses[i])[12]
    else:
        IP = str(addresses[i])[12] + str(addresses[i])[13]
    BSNode.users[i].IPLastByte = int(IP)

totalTime = 0
stateTracker = [0 for i in range(Parameters.userNum)]
ticker = 0
initialTime = time.time()


while True:

    if totalTime > ticker * 10:
        print 'elapsed time: ' + str(totalTime)
        ticker += 1

    start = time.time()

    # Determine the channel quality of all users
    RSSIs = subprocess.check_output(['/bin/bash','chanEst.sh'],shell=False)
    s = -1
    a = -1
    while s < len(RSSIs):
        s += 1
        userNo = -1
	if a == len(RSSIs):
	    break
        if RSSIs[s] == 'u' and RSSIs[s + 7] == ',':
            userNo = int(RSSIs[s + 6])
            a = s + 8
        elif RSSIs[s] == 'u' and RSSIs[s + 8] == ',':
            userNo = int(RSSIs[s + 6] + RSSIs[s + 7])
            a = s + 9
        string = ''
	
        while a < len(RSSIs) and RSSIs[a] != 'u':
            string += RSSIs[a]
            a += 1

        s = a - 1
        for i in range(Parameters.userNum):
            if userNo >= 0 and BSNode.users[i].IPLastByte == userNo:
                BSNode.users[i].rssi = int(string)
    scheduledUser = BSNode.schedule()
    #print scheduledUser
    newSegment = BSNode.NextSegmentsToSend(scheduledUser)
    BSNode.transmit(newSegment,Sockets,scheduledUser)
#    for i in range(Parameters.userNum):
#	print BSNode.users[i].stats.receiverBuffer
#	print BSNode.users[i].buffer
#    print '+++++++++++++++++++'	    
    end = time.time()
    totalTime += end - start

    if totalTime >= Parameters.totSimTime:
        break
for i in range(Parameters.userNum):
    Sockets.cliSockets[i].send("finished!")

Sockets.closeConnection()

#meanLayerRatio = numpy.mean([BSNode.users[u].stats.layerRatio() for u in range(Parameters.userNum)])
meanChannel = numpy.mean([BSNode.users[u].stats.averageRate() for u in range(Parameters.userNum)])
meanRebuf = numpy.mean([BSNode.users[u].stats.rebuf for u in range(Parameters.userNum)])
meanReward = numpy.mean([BSNode.users[u].stats.totalReward for u in range(Parameters.userNum)])

print meanReward, meanRebuf/totalTime,meanChannel
for l in range(Parameters.numLayer):
    print numpy.mean([BSNode.users[u].stats.receiverBuffer[l] for u in range(Parameters.userNum)])

print 'statistics for each user: '
for i in range(Parameters.userNum):
	print BSNode.users[i].stats.totalReward,BSNode.users[i].stats.rebuf/totalTime,BSNode.users[i].stats.receiverBuffer[0],BSNode.users[i].stats.receiverBuffer[1],BSNode.users[i].stats.receiverBuffer[2]
	BSNode.users[i].stats.writeFiles(i+1)
