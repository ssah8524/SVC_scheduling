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
        self.discTimeActive = [0.0 for i in range(parameters.chanStates * (parameters.bufferLimit + 1)**parameters.numLayer)]
        self.discTimePassive = [0.0 for i in range(parameters.chanStates * (parameters.bufferLimit + 1)**parameters.numLayer)]
        self.rebuffSlots = []
    def layerRatio(self): #For now this works for two layers only
        if float(self.receiverBuffer[0] + self.receiverBuffer[1]) != 0:
            return float(self.receiverBuffer[0])/float(self.receiverBuffer[0] + self.receiverBuffer[1])
        else:
            return 0
    def finalReward(self,parameters):
        return numpy.inner(self.discTimeActive,parameters.rewardVector) + numpy.inner(self.discTimePassive,parameters.rewardVector)
    def averageRate(self):
        return numpy.mean(self.chanStateTraj)
    def writeFiles(self,userIndex):
        outputReward = open('reward_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputRebuf = open('rebuf_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputChanTraj = open('trajectory_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputLayerRatio = open('layer_ratio_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputRebufSlots = open('rebuf_slots_' + str(userIndex) + '_' + sys.argv[5] + '.csv','a')
        outputReward.write(str(self.finalReward))
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
        self.capacity = int(sys.argv[2])
        self.timeSlot = float(sys.argv[3]) #duration of one scheduling slot
        self.totSimTime = int(sys.argv[4]) #duration of the entire simulation
        self.bufferLimit = 20
        self.chanStates = 4
        self.numLayer = 2
        self.preFetchThreshold = 2
        self.discount = 0.99
        self.epsilon = 0.01
        self.rateVector = [1,2,6,12] #This needs to be determined by the channel shaping method.
        self.primal = [0.0 for i in range(self.chanStates * (self.bufferLimit + 1)**self.numLayer)]
        self.dualActive = [0.0 for i in range(self.chanStates * (self.bufferLimit + 1)**self.numLayer)]
        self.dualPassive = [0.0 for i in range(self.chanStates * (self.bufferLimit + 1)**self.numLayer)]
        self.rewardVector = [0.0 for i in range(self.chanStates * (self.bufferLimit + 1)**self.numLayer)]
    def createVectors(self):
        prim = open('alg_files/x_1.csv','r')
        cost0 = open('alg_files/cost_0.csv','r')
        cost1 = open('alg_files/cost_1.csv','r')
        reward = open('reward.csv','r')
        Rprim = prim.read()
        Rcost0 = cost0.read()
        Rcost1 = cost1.read()
        Reward = reward.read()
        prim.close()
        cost0.close()
        cost1.close()
        Rprim = Rprim.split("\n")
        Rcost0 = Rcost0.split("\n")
        Rcost1 = Rcost1.split("\n")
        Reward = Reward.split("\n")
        for i in range(self.chanStates * (self.bufferLimit + 1)**self.numLayer):
            self.primal[i] = float(Rprim[i])
            self.dualActive[i] = float(Rcost1[i])
            self.dualPassive[i] = float(Rcost0[i])
            self.rewardVector[i] = float(Reward[i])

class user:
    def __init__(self,parameters):
        # For now let's assume that all users start from an initially empty buffer
        self.param = parameters
        self.buffer = [0 for i in range(parameters.numLayer)]
        self.oldBuffer = [0 for i in range(parameters.numLayer)]
        self.nextToBeSent = [0 for l in range(parameters.numLayer)]
        self.chan = 0
        self.tc = 100
        self.prim = 0
        self.costActive = 0
        self.costPassive = 0
        self.rateAccum = 0.0
        self.bufTracker = 0.0
        self.receivedSegments = [0 for i in range(parameters.numLayer)]
        self.stats = statistics(parameters)
    def findMeasures(self):
        bufState = 0
        maxState = (self.param.bufferLimit + 1) ** self.param.numLayer
        for i in range(self.param.numLayer):
            bufState += (self.buffer[self.param.numLayer - i - 1]) * (self.param.bufferLimit + 1) ** i
        curState = self.chan * maxState + bufState
        self.prim = self.param.primal[curState]
        self.costActive = self.param.dualActive[curState]
        self.costPassive = self.param.dualPassive[curState]
        return curState
    def findNextChanState(self,txRate):
        nextState = 0
        for c in range(self.param.chanStates - 1):
            if c < self.param.chanStates - 2 and txRate > 0.5 * (self.param.rateVector[c] + self.param.rateVector[c + 1]) and txRate < 0.5 * (self.param.rateVector[c + 1] + self.param.rateVector[c + 2]):
                nextState = c + 1
        if txRate > 0.5 * (self.param.rateVector[self.param.chanStates - 2] + self.param.rateVector[self.param.chanStates - 1]):
            nextState = self.param.chanStates - 1
        return nextState

class scheduler:
    def __init__(self,mode,parameters):
        self.param = parameters
        self.users = [user(parameters) for i in range(parameters.userNum)]
        self.mode = mode
    def schedule(self):
        active_v = [0 for x in range(self.param.userNum)]
        if self.mode == 'optimal':
            valid_p = [x for x in range(self.param.userNum) if self.users[x].prim > 0]
            invalid = [x for x in range(self.param.userNum) if self.users[x].prim == 0]
            dualActive = [self.users[x].costActive for x in range(self.param.userNum)]
            dualPassive = [self.users[x].costPassive for x in range(self.param.userNum)]

            remain = self.param.capacity - len(valid_p)
            if remain == 0: ##For the case where the primal step is sufficient
                for i in valid_p:
                    active_v[i] = 1
            elif remain > 0:
                dual = dualActive
                for i in valid_p:
                    active_v[i] = 1
                    dual[i] = 10000000
                while remain > 0:
                    a = find_minmax(dual, lambda x: x == min(dual))
                    ind = [i for i in a if active_v[i] != 1]
                    if len(ind) <= remain:
                        for i in range(len(ind)):
                            dual[ind[i]] = 100000000
                            active_v[ind[i]] = 1
                            remain -= 1
                    else: #If correct, program will enter this part only once at the end
                        index = tie_breaker(self.users,ind,remain)
                        for i in range(len(index)):
                            active_v[index[i]] = 1
                        remain = 0
            else:
                dual = dualPassive
                for i in invalid:
                    dual[i] = -10000000
                count = 0
                while count < self.param.capacity:
                    a = find_minmax(dual, lambda x: x == max(dual))
                    ind = [i for i in a if active_v[i] != 1]
                    if len(ind) <= self.param.capacity - count:
                        for i in range(len(ind)):
                            dual[ind[i]] = -100000000
                            active_v[ind[i]] = 1
                            count += 1
                    else: #If correct, program will enter this part only once at the end
                        index = tie_breaker(self.users,ind,self.param.capacity - count)
                        for i in range(len(index)):
                            active_v[index[i]] = 1
                        count = self.param.capacity
            if sum(active_v) != self.param.capacity:
                print 'ERROR!'


        elif self.mode == 'maxrate':
            cur_rates = [0 for x in range(self.param.userNum)]
            for u in range(self.param.userNum):
                cur_rates[u] = self.param.rateVector[self.users[u].chan]
            remain = self.param.capacity
            while remain > 0:
                candidate = find_minmax(cur_rates, lambda x: x == max(cur_rates))
                p = len(candidate)
                if p > remain: #randomly choose between them
                    for i in range(remain):
                        k = random.randint(0,len(candidate)-1)
                        active_v[candidate[k]] = 1
                        candidate.pop(k)
                elif p < remain:
                    for i in range(p):
                        active_v[candidate[i]] = 1
                        cur_rates[candidate[i]] = -1
                else:
                    for i in range(p):
                        active_v[candidate[i]] = 1
                remain -= p
            if sum(active_v) != self.param.capacity:
                print 'ERROR!'


        elif self.mode == 'pf':
            propRates = [0.0 for x in range(self.param.userNum)]
            for u in range(self.param.userNum):
                if self.users[u].rateAccum == 0:
                    denom = 0.01
                else:
                    denom = self.users[u].rateAccum
                propRates[u] = self.param.rateVector[self.users[u].chan] / denom
            remain = self.param.capacity
            while remain > 0:
                candidate = find_minmax(propRates, lambda x: x == max(propRates))
                p = len(candidate)
                if p > remain: #randomly choose between them
                    for i in range(remain):
                        k = random.randint(0,len(candidate)-1)
                        active_v[candidate[k]] = 1
                        candidate.pop(k)
                elif p < remain:
                    for i in range(p):
                        active_v[candidate[i]] = 1
                        propRates[candidate[i]] = -1
                else:
                    for i in range(p):
                        active_v[candidate[i]] = 1
                remain -= p
            if sum(active_v) != self.param.capacity:
                print 'ERROR!'

        elif self.mode == 'heuristic':
            finalIndex = [0 for u in range(self.param.userNum)]

            for u in range(self.param.userNum):
                if self.users[u].bufTracker <= 0:
                    finalIndex[u] = self.param.bufferLimit + self.users[u].chan
                else:
                    finalIndex[u] = self.param.bufferLimit - self.users[u].buffer[0]
            remain = self.param.capacity
            while remain > 0:
                candidates = find_minmax(finalIndex, lambda x: x == max(finalIndex))
                if len(candidates) <= remain:
                    for i in range(len(candidates)):
                        active_v[candidates[i]] = 1
                        finalIndex[candidates[i]] = -1
                    remain -= len(candidates)
                else:
                    # Systematically break ties.
                    if finalIndex[candidates[0]] > self.param.bufferLimit:
                        subs = [self.users[u].buffer[0] for u in candidates]
                        newCandidates = find_minmax(subs, lambda x: x == min(subs))
                    else:
                        subs = [self.users[u].chan for u in candidates]
                        newCandidates = find_minmax(subs, lambda x: x == max(subs))

                    if len(newCandidates) <= remain:
                        for i in range(len(newCandidates)):
                            active_v[candidates[newCandidates[i]]] = 1
                            finalIndex[candidates[newCandidates[i]]] = -1
                        remain -= len(newCandidates)
                    else:
                        k = random.randint(0,len(newCandidates) - 1)
                        if active_v[candidates[newCandidates[k]]] != 1:
                            active_v[candidates[newCandidates[k]]] = 1
                            candidates.pop(newCandidates[k])
                            newCandidates.pop(k)
                            remain -= 1
        elif self.mode == 'maxurgency':
            curBase = [self.users[u].buffer[0] for x in range(self.param.userNum)]
            remain = self.param.capacity
            while remain > 0:
                candidate = find_minmax(curBase, lambda x: x == min(curBase))
                p = len(candidate)
                if p > remain: #randomly choose between them
                    for i in range(remain):
                        k = random.randint(0,len(candidate)-1)
                        active_v[candidate[k]] = 1
                        candidate.pop(k)
                elif p < remain:
                    for i in range(p):
                        active_v[candidate[i]] = 1
                        curBase[candidate[i]] = self.param.bufferLimit + 1
                else:
                    for i in range(p):
                        active_v[candidate[i]] = 1
                remain -= p

            if sum(active_v) != self.param.capacity:
                print 'ERROR!'

        for i in range(self.param.userNum):
            if active_v[i] == 1:
                self.users[i].rateAccum = (1 - 1.0/self.users[i].tc)*self.users[i].rateAccum + (1.0/self.users[i].tc)*self.param.rateVector[self.users[i].chan]
                self.users[i].bufTracker += self.param.epsilon * ((self.users[i].buffer[0] - self.users[i].oldBuffer[0]) + self.users[i].buffer[1] - self.users[i].oldBuffer[1])
            else:
                self.users[i].rateAccum = (1 - 1.0/self.users[i].tc)*self.users[i].rateAccum
                self.users[i].bufTracker -= self.param.epsilon
                #print self.users[i].bufTracker, self.users[i].buffer, self.users[i].oldBuffer
        return active_v

    def NextSegmentsToSend(self,activeVector):
        sendBuffer = [fileBuffer(self.param) for u in range(self.param.userNum)]

        for u in range(self.param.userNum):

            self.users[u].oldBuffer = [self.users[u].buffer[l] for l in range(self.param.numLayer)]

            if self.users[u].buffer[0] == 0: #Take re-buffering into account
                self.users[u].stats.rebuf += self.param.timeSlot
                self.users[u].stats.rebuffSlots.append(totalTime)
            else:
                for l in range(self.param.numLayer):
                    self.users[u].buffer[l] = max(self.users[u].buffer[l] - 1,0)

            if activeVector[u] == 1:
                headOfLine = [self.users[u].nextToBeSent[l] for l in range(self.param.numLayer)]
                res = self.param.rateVector[self.users[u].chan] #This needs more effort
                tempBuf = [self.users[u].buffer[l] for l in range(self.param.numLayer)]

                dif = [0 for i in range(self.param.numLayer)]
                dif[self.param.numLayer - 1] = self.param.preFetchThreshold - 1
                for k in range(self.param.numLayer - 1):
                    dif[k] = tempBuf[k] - tempBuf[k + 1]
                for s in range(res):
                    for r in range(self.param.numLayer):
                        tmp = tempBuf[r]
                        if dif[r] < self.param.preFetchThreshold and tmp < self.param.bufferLimit:
                            tempBuf[r] = tmp + 1
                            sendBuffer[u].buffer[r].insert(len(sendBuffer[u].buffer[r]),headOfLine[r])
                            headOfLine[r] += 1
                            dif[self.param.numLayer - 1] = self.param.preFetchThreshold - 1
                            for k in range(self.param.numLayer - 1):
                                dif[k] = tempBuf[k] - tempBuf[k + 1]
                            break
                sendBuffer[u].sortRequestedSegments()
        return sendBuffer
    def transmit(self,queue,sockets,activeVector):
        breakUser = False
        breakLayer = False
        startTime = time.time()
        for i in range(self.param.userNum):
            if activeVector[i] == 1:
                for l in range(self.param.numLayer):
                    for f in queue[i].buffer[l]:
                        if f % 30 < 10:
                            segString = '0' + str(f % 30)
                        else:
                            segString = str(f % 30)
                        fileName = 'layer' + str(l) + '_' + segString + '.svc'
                        sockets.transmitFile(fileName,i)
                        self.users[i].buffer[l] += 1
                        self.users[i].stats.receiverBuffer[l] += 1
                        self.users[i].nextToBeSent[l] = max(queue[i].buffer[l]) + 1
            sockets.cliSockets[i].sendall("sfinished")
            txRate = float(sockets.cliSockets[i].recv(5))
            self.users[i].chan = self.users[i].findNextChanState(txRate)
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
        #self.host = socket.gethostname()
        self.host = "192.168.0.100"
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
Parameters.createVectors()
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

    for i in range(Parameters.userNum):
        stateTracker[i] = BSNode.users[i].findMeasures()

    start = time.time()
    scheduledUsers = BSNode.schedule()
    for i in range(Parameters.userNum):
        if scheduledUsers[i] == 1:
            BSNode.users[i].stats.discTimeActive[stateTracker[i]] += Parameters.discount**totalTime
        else:
            BSNode.users[i].stats.discTimePassive[stateTracker[i]] += Parameters.discount**totalTime

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
meanReward = numpy.mean([BSNode.users[u].stats.finalReward(Parameters) for u in range(Parameters.userNum)])
meanChannel = numpy.mean([BSNode.users[u].stats.averageRate() for u in range(Parameters.userNum)])
meanRebuf = numpy.mean([BSNode.users[u].stats.rebuf for u in range(Parameters.userNum)])

print meanReward, meanRebuf, meanRebuf/totalTime

for i in range(Parameters.userNum):
    BSNode.users[i].stats.writeFiles(i+1)

