from typing import Tuple

class CommChannel():
    def __init__(self,agents,noised=False) -> None:
        self.noised = noised
        self.agents = agents
        for agent in self.agents:
            agent.setChannel(self)

    def addNoise(self,message):
        noisedMsg = message

        return noisedMsg

    def encodeMessage(self,msg):
        return msg

    def decodeMessage(self,msg):
        return msg

    def sendMessage(self,senderID,receiverID,msg,tag):
        # print(tag,msg)
        receiver = self.agents[receiverID]
        encoded = self.encodeMessage(msg)
        if self.noised:
            encoded = self.addNoise(encoded)
        decoded = self.decodeMessage(encoded)
        receiver.recieveMessage(senderID,decoded,tag)


    