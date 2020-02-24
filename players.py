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
    reservations = {} #Dictionnary of reservation times of the player
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

    def newadvance(self,loss,wait):
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
        raise Exception("Not implemented")

    def treated(self,state,packet_id,time,mu):
        """
        @brief: Updates the parameters after a packet has been processed
        @param state: 1 if the packet have been successfully processed, 0 if the packet have been lost
        @param packet_id: The id of the processed packet
        @param time: The time when the packet have been processed
        @param mu: the parameter mu of the server
        @return: 
        """
        raise Exception("Not implemented")

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

class RandomPlayer(Player):

    def __init__(self):
        self.name = "Random" 
        self.reservations = {}

    def newadvance(self,loss,wait):
        return np.random.random()

    def reserve(self,time,ar_time,j):
        self.advance = (ar_time-time)*np.random.random()
        self.reservations[j] = ((time+self.advance,ar_time))
        return self.reservations[j][0]
    
    def treated(self,state,packet_id,time,mu):
        wait = time - self.reservations[packet_id][1] - mu
        self.update_stats(1-state,wait,mu)

class CarefulPlayer(Player):

    def __init__(self):
        self.name = "Careful" 
        self.reservations = {}

    def newadvance(self,loss,wait):
        return 0

    def reserve(self,time,ar_time,j):
        self.reservations[j] = (ar_time,ar_time)
        return self.reservations[j][0]
    
    def treated(self,state,packet_id,time,mu):
        wait = time - self.reservations[packet_id][1] - mu
        self.update_stats(1-state,wait,mu)

class StrategicPlayerAlpha(Player):

    def __init__(self,name,alpha):
        self.name = "Strategic "+name+r" ($\alpha$="+str(alpha)+")"
        self.alpha = alpha
        self.reservations = {}

    def newadvance(self,loss,wait):
        self.advance = max(0,self.advance+wait-self.alpha*loss)

    def reserve(self,time,ar_time,j):
        self.reservations[j] = (max(time,ar_time-self.advance),ar_time)
        return self.reservations[j][0]
    
    def treated(self,state,packet_id,time,mu):
        loss = 1-state
        wait = time - self.reservations[packet_id][1] - mu
        self.update_stats(loss,wait,mu)
        wait = max(0,wait)
        #vprint("Updating advance")
        #vprint(f"Packet was sent at {self.reservations[packet_id][0]}, arriving at {self.reservations[packet_id][1]}")
        #vprint(f"Packet was received back at {time}")
        #vprint(f"Waiting time: {time-self.reservations[packet_id][1]}. Loss: {loss}")
        self.newadvance(loss,wait)
        #vprint(f"New advance: {self.advance}")

class StrategicPlayer(Player):

    def __init__(self,name):
        self.name = "Strategic "+name
        self.reservations = {}
        self.wmax = 1

    def newadvance(self,loss,wait):
        self.wmax = max(wait,self.wmax)
        self.advance = max(0,self.advance+wait/self.wmax)

    def reserve(self,time,ar_time,j):
        self.reservations[j] = (max(time,ar_time-self.advance),ar_time)
        return self.reservations[j][0]
    
    def treated(self,state,packet_id,time,mu):
        loss = 1-state
        wait = time - self.reservations[packet_id][1] - mu
        self.update_stats(loss,wait,mu)
        #vprint("Updating advance")
        #vprint(f"Packet was sent at {self.reservations[packet_id][0]}, arriving at {self.reservations[packet_id][1]}")
        #vprint(f"Packet was received back at {time}")
        #vprint(f"Waiting time: {time-self.reservations[packet_id][1]}. Loss: {loss}")
        self.newadvance(loss,wait)
        #vprint(f"New advance: {self.advance}")

class MixedAlphaPlayer(Player):

    def __init__(self,name,alpha):
        self.name = "Mixed "+name
        self.reservations = {}
        self.wmax = 1
        self.alpha = alpha

    def newadvance(self,loss,wait):
        self.wmax = max(wait,self.wmax)
        self.advance = max(0,self.advance+wait/self.wmax-self.alpha*loss)

    def reserve(self,time,ar_time,j):
        self.reservations[j] = (max(time,ar_time-self.advance),ar_time)
        return self.reservations[j][0]
    
    def treated(self,state,packet_id,time,mu):
        loss = 1-state
        wait = time - self.reservations[packet_id][1] - mu
        self.update_stats(loss,wait,mu)
        #vprint("Updating advance")
        #vprint(f"Packet was sent at {self.reservations[packet_id][0]}, arriving at {self.reservations[packet_id][1]}")
        #vprint(f"Packet was received back at {time}")
        #vprint(f"Waiting time: {time-self.reservations[packet_id][1]}. Loss: {loss}")
        self.newadvance(loss,wait)
        #vprint(f"New advance: {self.advance}")

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