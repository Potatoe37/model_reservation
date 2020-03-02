from random import randint
import numpy as np
from functions import vprint

class Player:
    name = "" #The name of the player
    nu = 50 #The nu of the player
    lbda = 50 #The lambda of the player
    alpha = 50 #The factor alpha of the player
    initial_alpha = 50
    advance = 0 #How long in advance the player will reserve
    arrival_times = [] #List of real arrival times of all packets
    revelation = [] #List of revelation times for the packets
    reservations = {} #Dictionnary of reservation times of the player (res_time,ar_time)
    advances = {} #Dictionnary of advances used for each packet (!=ar_time-res_time)
    total_loss = 0 #Total packets lost by the player
    total_waiting_time = 0 #The total waiting time of the player
    processed = 0 #Number of packets processed
    memory = 10 #How far the player remembers of the game  
    memory_loss = 0 #The loss of the player as far back as he can remember
    advances_mem = [0 for i in range(memory)]
    advance_mean_mem = 0
    wmax = 1 #The maximum maiting time

    def nexttime(self,time):
        """
        @brief: 
        @param time: The last packet arrival time
        @return: The nex packet arrival time
        """
        return time+np.random.exponential(self.lbda)

    def newadvance(self,loss,wait,advance):
        """
        @brief: Computes the new advance for teh player
        @param loss: The total loss as far back as the player can remember
        @param wait: The total wait time as far back as the player can remember
        @return: None
        """
        raise Exception("Not implemented")

    def reserve(self,time,ar_time,j):
        """
        @brief: For the given current time and the arrival time of a packet, computes the reservation time for this packet
        @param time: the current time
        @param ar_time: the arrival time of the packet
        @return: the reservation time for the packet
        """
        self.reservations[j] = (max(time,ar_time-self.advance),ar_time)
        self.advances[j] = self.advance 
        return self.reservations[j][0]

    def update_stats(self,loss,wait,mu):
        # The packet as lost
        if loss==1:
            #self.alpha *= 2
            self.total_loss += 1
        # The packet was processed
        else:
            self.processed += 1
            #self.alpha = self.initial_alpha
            self.total_waiting_time += wait+mu
    
    def treated(self,state,packet_id,time,mu):
        """
        @brief: Updates the parameters after a packet has been processed
        @param state: 1 if the packet have been successfully processed, 0 if the packet have been lost
        @param packet_id: The id of the processed packet
        @param time: The time when the packet have been processed
        @param mu: the parameter mu of the server
        @return: 
        """
        loss = 1-state
        wait = time - self.reservations[packet_id][1] - mu
        advance = self.advances[packet_id]
        self.update_stats(loss,wait,mu)
        #vprint("Updating advance")
        #vprint(f"Packet was sent at {self.reservations[packet_id][0]}, arriving at {self.reservations[packet_id][1]}")
        #vprint(f"Packet was received back at {time}")
        #vprint(f"Waiting time: {time-self.reservations[packet_id][1]}. Loss: {loss}")
        self.newadvance(loss,wait,advance)
        self.reservations[packet_id] = (-1,-1)
        for j in self.reservations:
            if self.reservations[j][0]>time:
                self.reserve(time,self.reservations[j][1],j)
        #vprint(f"New advance: {self.advance}")
        return self.reservations

class RandomPlayer(Player):

    def __init__(self):
        self.name = "Random" 
        self.reservations = {}

    def newadvance(self,loss,wait,advance):
        self.advance = np.random.random()
        

class CarefulPlayer(Player):

    def __init__(self):
        self.name = "Careful" 
        self.reservations = {}

    def newadvance(self,loss,wait,advance):
        return 0

class StrategicPlayerAlpha(Player):

    def __init__(self,name,alpha):
        self.name = "Strategic "+name+r" ($\alpha$="+str(alpha)+")"
        self.alpha = alpha
        self.reservations = {}

    def newadvance(self,loss,wait,advance):
        wait = max(0,wait)
        self.advance = max(0,advance+wait-self.alpha*loss)

class StrategicPlayer(Player):

    def __init__(self,name):
        self.name = "Strategic "+name
        self.reservations = {}
        self.wmax = 1

    def newadvance(self,loss,wait,advance):
        self.wmax = max(wait,self.wmax)
        self.advance = max(0,self.advance+wait/self.wmax)
    
class MixedAlphaPlayer(Player):

    def __init__(self,name,alpha):
        self.name = "Mixed "+name
        self.reservations = {}
        self.wmax = 1
        self.alpha = alpha

    def newadvance(self,loss,wait,advance):
        self.wmax = max(wait,self.wmax)
        self.advance = max(0,self.advance+wait/self.wmax-self.alpha*loss)

class LearningMyopic(Player):

    def __init__(self, name):
        self.name = "LearnerMyopic"
        self.reservations = {}
        self.beta = 0.8

    def newadvance(self,loss,wait,advance):
        if wait >0:
            self.advance = self.advance + self.beta*wait
        else:
            self.advance = max(0,self.advance / 2-0.1)
            #self.beta *= 0.9

class LearningAverage(Player):

    def __init__(self, name):
        self.name = "LearnerAverage"
        self.reservations = {}
        self.alpha = 100
        self.weightedWait = 0
        self.weightedLoss = 0

    def newadvance(self,loss,wait,advance):
        self.weightedWait = 0.1*wait + 0.9*self.weightedWait
        self.weightedLoss = 0.1*loss + 0.9*self.weightedLoss
        self.advance = max(0,self.advance + self.weightedWait - self.alpha*self.weightedLoss)

random1 = RandomPlayer()
mixal0 = MixedAlphaPlayer("MixAlpha0",1)
mixal1 = MixedAlphaPlayer("MixAlpha1",10)
mixal2 = MixedAlphaPlayer("MixAlpha2",100)
mixal3 = MixedAlphaPlayer("MixAlpha3",1000)
alpha0 = StrategicPlayerAlpha("Alpha0",1)
alpha1 = StrategicPlayerAlpha("Alpha1",10)
alpha2 = StrategicPlayerAlpha("Alpha2",100)
alpha3 = StrategicPlayerAlpha("Alpha3",1000)
strat1 = StrategicPlayer("Boss1")
caref1 = CarefulPlayer()
myopic = LearningMyopic("")
average = LearningAverage("")