import numpy as np
from Environment.EnvUtilities import decodeAction, transition
from collections import defaultdict

def defaultVal():
    return 0

class MessageRecoverer():
    def __init__(self, id, totalTreatNum) -> None:
        self._guidePosRecord = defaultdict(defaultVal)
        self._treatPosRecord = defaultdict(defaultVal)
        self._anchoredGuidePos = None
        self._anchoredTreatPos = None
        self._id = id
        self._totalTreatNum = totalTreatNum
        self._checksumWeight = 3

    def computeAnchor(self, type, correctChecksum, position):
        increment = 1
        if correctChecksum:
            increment *= self._checksumWeight
        if type == "G":
            self._guidePosRecord[tuple(position)] += increment
            # print("Guide Pos: ", self._guidePosRecord)
            self._anchoredGuidePos = max(
                self._guidePosRecord, key=self._guidePosRecord.get)
        else:
            self._treatPosRecord[tuple(position)] += increment
            # print("Treat Pos: ", self._treatPosRecord)
            self._anchoredTreatPos = max(
                self._treatPosRecord, key=self._treatPosRecord.get)

    def computeGuideAnchor(self, position: np.array, correctChecksum: bool):
        # sets guide anchor position
        self.computeAnchor("G", correctChecksum, position)

    def computeTreatAnchor(self, position: np.array, correctChecksum: bool):
        # sets treat anchor position
        self.computeAnchor("T", correctChecksum, position)

    def findRecallIndex(self,recievedHistory):
        i = len(recievedHistory)
        while i > 0:
            i-=1
            if recievedHistory[i]["checksum"]:
                return i
        return -1

    def recall(self,recievedHistory,recallIndex):
        s = recievedHistory[recallIndex]["state"][self._id]
        sPrimes = recievedHistory[recallIndex]["sPrime"]
        if sPrimes:
            sPrime = sPrimes[self._id]
        else:
            sPrime = s
        for i in range(recallIndex+1,len(recievedHistory)):
            if recievedHistory[i]["sPrime"] is not None:
                s = sPrime
                actionTaken = decodeAction(recievedHistory[i]["action"][0])
                sPrime = np.array(
                    transition(tuple(s), actionTaken), dtype=np.uint8)

        return sPrime
            

    def resolveMyStates(self, recievedHistory, fixedState, action, hasSPrime, fixedsPrime):
        # Current scout's state and s' can be estimated using previous s and action

        recallIndex = self.findRecallIndex(recievedHistory)
        if recallIndex != -1:
            s = self.recall(recievedHistory,recallIndex)
        else:
            recentRecord = recievedHistory[-1]
            history = recentRecord["sPrime"] or recentRecord["state"]
            s = history[self._id]
        actionTaken = decodeAction(action[0])
        sPrime = np.array(
            transition(tuple(s), actionTaken), dtype=np.uint8)
        fixedState[self._id*2:self._id*2 +
                    2] = s
        if hasSPrime:
            fixedsPrime[self._id*2:self._id*2 + 2] = sPrime

    def resolveOtherStates(self, recievedHistory, otherAgentID):
        # resolving other agents' s and s'
        otherAgentStates = []
        startRecall = False
        for record in recievedHistory:
            startRecall = startRecall or record["checksum"]
            if startRecall:
                agentS = record["state"][otherAgentID]
                agentSPrime = record["sPrime"]
                if agentSPrime is not None:
                    agentSPrime = agentSPrime[otherAgentID]
                otherAgentStates.append([agentS, agentSPrime])

    def attemptRecovery(self, senderID, parse, recievedHistory, action):
        # Attempt in recovering original message by looking at history of correctly received messages
        # Could be checksum got corrupted, msg got corrupted or both
        fixedState = parse["state"]
        fixedsPrime = parse["sPrime"]
        hasSPrime = fixedsPrime is not None
    
        # currently hardcoded for 2 scouts environment but can be extended to more agent scenarios
        if self._id == 1:
            otherAgentID = 2
        else:
            otherAgentID = 1

        # Guide, treat positions are fixed hence can be recovered directly from anchored position
        if self._anchoredGuidePos is not None:
            fixedState[0:2] = self._anchoredGuidePos
            if hasSPrime:
                fixedsPrime[0:2] = self._anchoredGuidePos

        if self._anchoredTreatPos is not None:
            treatStart = len(fixedState) - 2*self._totalTreatNum
            fixedState[treatStart:] = self._anchoredTreatPos
            if hasSPrime:
                fixedsPrime[treatStart:] = self._anchoredTreatPos

        if recievedHistory:
            self.resolveMyStates(recievedHistory, fixedState,
                                 action, hasSPrime, fixedsPrime)

            self.resolveOtherStates(recievedHistory, otherAgentID)

        return {
            "state": fixedState,
            "reward": parse["reward"],
            "sPrime": fixedsPrime
        }
