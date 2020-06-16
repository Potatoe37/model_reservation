from random import randint
import numpy as np
from functions import vprint

class Player:
    name = "" #The name of the player
    nu = 500 #The nu of the player
    lbda = 50 #The lambda of the player
    mu = 1 #The mu of the game
    n_players = 1 #The number of players of the game
    alpha = 50 #The factor alpha of the player
    initial_alpha = 50
    advance = 0 #How long in advance the player will reserve
    arrival_times = [] #List of real arrival times of all packets
    revelation = [] #List of revelation times for the packets
    reservations = {} #Dictionnary of reservation times of the player (res_time,ar_time)
    advances = {} #Dictionnary of the advances at the time of the reservation for each packet
    total_loss = 0 #Total packets lost by the player
    total_waiting_time = 0 #The total waiting time of the player
    processed = 0 #Number of packets processed
    memory = 10 #How far the player remembers of the game  
    memory_loss = 0 #The loss of the player as far back as he can remember
    advances_mem = [0 for i in range(memory)]
    advance_mean_mem = 0
    wmax = 1 #The maximum maiting time

    def get_param(self,mu,lbda,n_players):
        self.mu = mu
        if lbda!=0: 
            self.lbda = lbda
        self.n_players = n_players

    def nexttime(self,time):
        """
        @brief: 
        @param time: The last packet arrival time
        @return: The next packet arrival time
        """
        return time+np.random.exponential(self.lbda)

    def newadvance(self,loss,wait,used_advance,param_advance):
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

    def update_stats(self,loss,wait):
        # The packet as lost
        if loss==1:
            #self.alpha *= 2
            self.total_loss += 1
        # The packet was processed
        else:
            self.processed += 1
            #self.alpha = self.initial_alpha
            self.total_waiting_time += wait
    
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
        wait = time - self.reservations[packet_id][1]
        used_advance = self.reservations[packet_id][1]-self.reservations[packet_id][0]
        param_advance = self.advances[packet_id]
        self.update_stats(loss,wait)
        #vprint("Updating advance")
        #vprint(f"Packet was sent at {self.reservations[packet_id][0]}, arriving at {self.reservations[packet_id][1]}")
        #vprint(f"Packet was received back at {time}")
        #vprint(f"Waiting time: {time-self.reservations[packet_id][1]}. Loss: {loss}")
        self.newadvance(loss,wait,used_advance,param_advance)
        self.reservations[packet_id] = (-1,-1)
        for j in self.reservations: #Update all reservations with the new advance
            if self.reservations[j][0]>time:
                self.reserve(time,self.reservations[j][1],j)
        #vprint(f"New advance: {self.advance}")
        return self.reservations

class RandomPlayer(Player):

    def __init__(self):
        self.name = "Random" 
        self.reservations = {}

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.advance = np.random.random()
        

class CarefulPlayer(Player):

    def __init__(self):
        self.name = "Careful" 
        self.reservations = {}
        self.lbda = 5/0.01

    def newadvance(self,loss,wait,used_advance,param_advance):
        return 0

class StrategicPlayerAlpha(Player):

    def __init__(self,name,alpha):
        self.name = "Strategic "+name+r" ($\alpha$="+str(alpha)+")"
        self.alpha = alpha
        self.initial_alpha = alpha
        self.reservations = {}

    def newadvance(self,loss,wait,used_advance,param_advance):
        wait = max(0,wait-self.mu)
        self.advance = max(0,used_advance+wait-self.alpha*loss)
        #Comment not to increase alpha
        if loss==1:
            self.alpha *= 2
        else:
            self.alpha = self.initial_alpha

class StrategicPlayer(Player):

    def __init__(self,name=""):
        self.name = "Strategic "+name
        self.reservations = {}
        self.wmax = 1

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.wmax = max(wait-self.mu,self.wmax)
        self.advance = max(0,used_advance+(wait-self.mu)/self.wmax)
    
class MixedAlphaPlayer(Player):

    def __init__(self,name,alpha):
        self.name = "Mixed "+name
        self.reservations = {}
        self.wmax = 1
        self.alpha = alpha

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.wmax = max(wait-self.mu,self.wmax)
        self.advance = max(0,used_advance+(wait-self.mu)/self.wmax-self.alpha*loss)

class LearningMyopic(Player):

    def __init__(self, name=""):
        self.name = "LearnerMyopic" + name
        self.reservations = {}
        self.beta = 0.8

    def newadvance(self,loss,wait,used_advance,param_advance):
        if wait >0:
            self.advance = self.advance + self.beta*(wait-self.mu)
        else:
            self.advance = max(0,self.advance / 2-0.1)
            #self.beta *= 0.9

class LearningAverage(Player):

    def __init__(self, name=""):
        self.name = "LearnerAverage" + name
        self.reservations = {}
        self.alpha = 100
        self.weightedWait = 0
        self.weightedLoss = 0

    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==0:
            self.weightedWait = 0.1*max(0,wait-self.mu) + 0.9*self.weightedWait
        self.weightedLoss = 0.1*loss + 0.9*self.weightedLoss
        self.advance = max(0,self.advance + self.weightedWait - self.alpha*self.weightedLoss)

class LearningAverageBien(Player):

    def __init__(self, name=""):
        self.name = "LearnerAverageBien" + name
        self.reservations = {}
        self.advances = {}
        self.alpha = 100
        self.weightedWait = 0
        self.weightedLoss = 0

    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==0:
            self.weightedWait = 0.1*(max(0,wait-self.mu)-(param_advance-used_advance)) + 0.9*self.weightedWait
        self.weightedLoss = 0.1*loss + 0.9*self.weightedLoss
        self.advance = max(0,self.advance + self.weightedWait - self.alpha*self.weightedLoss)

class StupidLearner(Player):

    def __init__(self,name=""):
        self.name = "Stupid" + name
        self.reservations = {}
        self.packets = 1
    
    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==0:
            self.advance += (np.exp(1/self.packets)-1)*100
        else:
            self.advance = max(0,self.advance-((np.exp(-(self.packets/100)))*100))
        self.packets += 1

class StupidSnail(Player):

    def __init__(self,name=""):
        self.name = "StupidSnail" + name
        self.reservations = {}
        self.packetspassed = 1
        self.packetslost = 1
    
    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==0:
            self.advance += 100/self.packetspassed
            self.packetspassed+=1
        else:
            self.advance = max(0,self.advance-100/self.packetslost)
            self.packetslost += 1

class EvolvedLearner(Player):

    def __init__(self,name=""):
        self.name = "Evolved" + name
        self.reservations = {}
        self.packets = 1
        self.weightedWait = 1
    
    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==0:
            self.weightedWait = 0.1*max(0,wait-self.mu) + 0.9*self.weightedWait
            self.advance += self.weightedWait*(np.exp(1/self.packets)-1)*100
        else:
            self.advance = max(0,self.advance-self.weightedWait*((np.exp(-(self.packets/100)))*100))
        self.packets += 1

class EvolvedSnail(Player):

    def __init__(self,name=""):
        self.name = "EvolvedSnail" + name
        self.reservations = {}
        self.packetspassed = 1
        self.packetslost = 1
        self.weightedWait = 1
    
    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==0:
            self.weightedWait = 0.1*max(0,wait-self.mu) + 0.9*self.weightedWait
            self.advance += self.weightedWait*100/self.packetspassed
            self.packetspassed+=1
        else:
            self.advance = max(0,self.advance-self.weightedWait*100/self.packetslost)
            self.packetslost += 1

class DeterministicMean(Player):

    def __init__(self, name=""):
        self.name = "DeterministicMedium"+name
        self.reservations = {}
        self.advance = 0
    
    def get_param(self,mu,lbda,n_players):
        self.mu = mu
        self.lbda = lbda
        self.n_players = n_players
        self.advance = 1/(1/self.mu-self.n_players/self.lbda)

    def newadvance(self,loss,wait,used_advance,param_advance):
        return 0

class StupidDeterministic(Player):

    def __init__(self, advance, name=""):
        self.name = "StupidDeterministic"+str(advance)+name
        self.reservations = {}
        self.advance = advance
        self.lbda = 5/0.99

    def newadvance(self,loss,wait,used_advance,param_advance):
        return 0

class SmartAnalyst(Player):

    def __init__(self,prob_threshold,name=""):
        self.name = "SmartAnalyst"+name
        self.reservations = {}
        self.threshold = 0
        self.prob_threshold = prob_threshold
        self.alpha = np.random.random()
        self.testedalphas = {}
        self.row = 0

    def get_param(self,mu,lbda,n_players):
        self.mu = mu
        self.lbda = lbda
        self.n_players = n_players
        self.threshold = -self.lbda*np.log(self.prob_threshold) #On recalcule après avoir obtenu le lambda du jeu

    def newadvance(self,loss,wait,used_advance,param_advance):
        if loss==1:
            self.advance=0  
            self.testedalphas[self.alpha] = self.row
            self.row = 0
            if len(self.testedalphas)<10:
                self.alpha = np.random.random() 
            else:
                total=0
                alpha=0
                for a in self.testedalphas:
                    total += self.testedalphas[a]
                    alpha += a*self.testedalphas[a]
                self.alpha = alpha/total
        else:
            self.row+=1
            if wait>self.threshold:
                self.advance+=self.alpha*wait

class RandomAnalyst(Player):

    def __init__(self,name=""):
        self.name = "RandomAnalyst"+name
        self.reservations = {}
        self.pempty = 0
    
    def get_param(self,mu,lbda,n_players):
        self.mu = mu
        self.lbda = lbda
        self.n_players = n_players
        self.pempty = 1-mu/lbda

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.advance = (self.n_players*self.mu/self.lbda)/(1/self.mu-self.n_players/self.lbda) if np.random.random()>self.pempty else 0

class RandomAdvancedAnalyst(Player):

    def __init__(self,name=""):
        self.name = "RandomAdvancedAnalyst"+name
        self.reservations = {}
        self.pempty = 0
    
    def get_param(self,mu,lbda,n_players):
        self.mu = mu
        self.lbda = lbda
        self.n_players = n_players
        self.pempty = 1-mu/lbda

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.advance = np.random.exponential(1/(1/self.mu-self.n_players/self.lbda)) if np.random.random()>self.pempty else 0


class Analyst(Player):

    def __init__(self,name=""):
        self.name = "Analyst"+name
        self.reservations = {}

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.advance = (self.n_players*self.mu/self.lbda)/(1/self.mu-self.n_players/self.lbda) if loss==0 else 0

class AlphaBetaConst(Player):

    def __init__(self,alpha,beta,name=""):
        self.name = "Alpha"+str(alpha)+"Beta"+str(beta)
        self.reservations = {}
        self.alpha = alpha
        self.beta = beta

    def newadvance(self,loss,wait,used_advance,param_advance):
        self.advance = max(0,self.advance - self.alpha*loss + self.beta*wait)

class Charging(Player):
    """
    Un joueur avec un seul gros paquet 
    """

    def __init__(self,size,name=""):
        self.name = "Charging"
        self.reservations = {}
        self.size = size
        self.advance = 0

    def newadvance(self,loss,wait,used_advance,param_advance):
        return 0

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
averageB = LearningAverageBien("")
stupid = StupidLearner("")
snail = StupidSnail("")
evolearn = EvolvedLearner("")
evosnail = EvolvedSnail("")
detmean = DeterministicMean()
stup1 = StupidDeterministic(1)
stup2 = StupidDeterministic(2)
stup3 = StupidDeterministic(3)
stup4 = StupidDeterministic(4)
stup5 = StupidDeterministic(5)
stup6 = StupidDeterministic(6)
stup7 = StupidDeterministic(7)
smartanalyst = SmartAnalyst(0.2)
randanalyst = RandomAnalyst()
randadvancedanalyst = RandomAdvancedAnalyst()
analyst = Analyst()
charging = Charging(100)