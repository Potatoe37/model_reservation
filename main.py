import players
import functions as funs
import plotparam as ppm
from functions import vprint

from copy import deepcopy
import numpy as np
import bisect
import time as tt
import pickle #Save lists data
import os.path

class Game:

    insttt = 0
    def insert_event(self,event):
        """
        @brief: Inserts an event in the sorted list of events
        @param event_time: The time of the event to insert
        @return: None
        """
        ttt = tt.time()
        bisect.insort(self.event_times,event)
        self.insttt += tt.time()-ttt
        return 0

    def __init__(self,players,lbda,initial_size=500,mu=0):
        """
        @brief: Initialisation of the game
        @param players: list of participationg players
        @param lbda: the parameter lambda of all players (mean time between two packets arrival)
        @param initial_size: how far the game is anticipated (default 50)
        @param mu: the parameter mu of the game (mean treatment time of a packet by the server) (default lbda/number of players)
        @return: Object Game
        """
        self.seed = 0
        #self.seed = int(np.random.random()*1000000)
        np.random.seed(self.seed)
        print(f"Seed = {self.seed}")
        self.keep_data = True #Saves the data in a file such that you don't make 2 times the same simulation
        self.use_data = True #True if you want to use your saved data, non if you want to execute the complete simulation even if it was already done
        self.new = True #The game haven't started yet
        self.initial_size = initial_size #The number of packets already created
        self.players = [deepcopy(p) for p in players]  #The list of players playing the game
        self.n_players = len(players) #The number of players
        self.lbda = lbda #The lambda of the game (mean arrival time for the players) #0 if different for each player
        self.event_times = [] #The list of times of next happening events (sorted), and, event type (0: revelation, 1: reservation, 2: treatment), player concerned, packet concerned
        self.event = (0,0,-1,-1)
        self.time = -1 #The time of the game
        if self.lbda==0:
            self.lbda = 1/sum([1/self.players[i].lbda for i in range(self.n_players)])
            print(self.lbda)
        if mu==0:
            if self.lbda==0:
                self.mu = (1/sum([1/self.players[i].lbda for i in range(self.n_players)]))/self.n_players/self.n_players #The mu of the game
            else:
                self.mu = self.lbda
        else:
            self.mu = mu #The mean treatment times of the packets
        #Giving mu, lambda and the number of players to each player
        for p in self.players:
            p.get_param(self.mu,lbda*self.n_players,self.n_players)
        print(f"mu={self.mu}")
        if self.mu<self.lbda:
            self.theoretical_wait = (self.mu/self.lbda)/(1/self.mu-1/self.lbda)
            self.theoretical_time_in_sys = 1/(1/self.mu-1/self.lbda)
        else:
            self.theoretical_wait = 'inf'
            self.theoretical_time_in_sys = 'inf'
        print(f"Theoretical mean wait: {self.theoretical_wait}")
        print(f"Theoretical mean time in sys: {self.theoretical_time_in_sys}")
        def initialisation(n_players,lbda,initial_size=50):
            """
            @brief: Creates the initail lists of arrival times and revelation times of each players
            @param n_players: the number of players
            @param lbda: the parameter lambda of the game
            @param initial_size: the size of the lists we will create
            @return: The list of dicts of arrival times and the list of list of revelation times
            """
            ar = []
            rev = []
            for i in range(n_players):
                nu = self.players[i].nu
                ari = {}
                revi = {}
                time = 0
                if self.players[i].name == "Charging":
                    #If the player is a charging player, he only have a heavy packet to send at the beginning
                    for j in range(self.players[i].size):
                        ari[j] = 0
                        revi[j] = 0
                        self.event_times.append((0,0,i,j))
                else:
                    for j in range(initial_size):
                        time += np.random.exponential(self.players[i].lbda)
                        revelation = max(0,time-2*nu*np.random.random())
                        ari[j] = time
                        revi[j] = revelation
                        self.event_times.append((revelation,0,i,j))
                ar.append(ari)
                rev.append(revi)
            self.event_times.sort()
            return ar,rev
        ar,rev = initialisation(self.n_players,lbda,initial_size)
        self.arrival_times = ar #List of the lists of the first 'initial_size' arrival times for all players
        self.last_arrival = [max(self.arrival_times[i].values()) for i in range(self.n_players)] #List of the last arrival time for each player (not to look for the max at every update)
        self.revelation = rev #List of the lists of the first 'initial_size' revelation times for all players
        self.reservations = [{} for i in range(self.n_players)] #List of the lists of the first 'initial_size' reservation times for all players (-1 if no reservation yet)
        for i in range(self.n_players):
            for j in range(initial_size):
                self.reservations[i][j] = -1
        #for i in range(self.n_players):
        #    self.players[i].reservations = self.reservations[i]
        self.packets = [] #The file of packets to treat (i,j,t,delta) for player i packet j, arriv time t, treatment time delta
        self.treatment = -1 #The remaining treatement time
        self.y = [[[0] for i in range(4)] for i in range(self.n_players)] #For plot
        self.times = []
        self.tota = []

        #ANALYSIS
        self.revttt = 0
        self.resttt = 0
        self.trettt = 0
        self.othttt = 0
        self.othttt2 = 0

        #Courbes données
        self.timeinfile = []
        self.packetsinfile = []

    def update(self,player_i,packet_id):
        """
        @brief: Updates the packets for player i, after one of his packets was treated, so his list of packets remains full 
        @param player_i: The player whose list of packets must be updated 
        @param packet_id: The id of the processed packet in the dictionnaries
        @return: None
        """
        nu = self.players[player_i].nu
        time = max(self.last_arrival[player_i],self.time) + np.random.exponential(self.players[player_i].lbda)
        self.last_arrival[player_i] = time 
        self.arrival_times[player_i][packet_id] = time
        self.revelation[player_i][packet_id] = max(self.time+0.01,time-2*nu*np.random.random())
        #print(f"AR TIME = {time}")
        #print(f"RV TIME = {self.revelation[player_i][packet_id]}")
        self.insert_event((self.revelation[player_i][packet_id],0,player_i,packet_id))
        self.reservations[player_i][packet_id] = -1
    
    def add_plot(self,player_i,packet_id,ar_time,loss):
        self.y[player_i][0].append(self.players[player_i].advance)
        self.y[player_i][1].append(self.y[player_i][1][-1]+max(0,self.time-ar_time))
        self.y[player_i][2].append(self.y[player_i][2][-1]+loss)
        self.y[player_i][3].append(self.time)
        f = open("data.txt",mode="a")
        f.write(f"{ar_time}\t{self.players[player_i].reservations[packet_id][0]}\t{self.time}\t{player_i}\t{ar_time-self.players[player_i].reservations[packet_id][0]}\t{loss}\n")
        f.close()

    def turn(self):
        # Reavealing arrival time to clients
        ttt=tt.time()
        self.time,event,i,j = self.event
        if event==0:
            #vprint(f"Revealing arrival time ({self.arrival_times[i][j]}) of packet {j} to player {i} ({self.players[i].name}) at time {self.time}.")
            res_time = self.players[i].reserve(self.time,self.arrival_times[i][j],j)
            #vprint(f"Player {i} ({self.players[i].name}) reserves at time {res_time} for packet {j} arriving at time {self.arrival_times[i][j]}.")
            self.reservations[i][j] = res_time
            self.insert_event((res_time,1,i,j))
        self.revttt+=tt.time()-ttt
        # Reserving a place in the queue
        ttt=tt.time()
        if event==1:
            #vprint(f"Player {i} ({self.players[i].name}) reserved at time {self.time} for packet {j}.")
            self.packets.append((i,j,self.arrival_times[i][j],np.random.exponential(self.mu)))
            #vprint(f"Adding packet {j} to packets queue...")
            #vprint(f"Queue state: {self.packets}")
        self.resttt+=tt.time()-ttt
        # Treating packets
        ttt=tt.time()
        if self.packets!=[]:    
            if self.treatment<self.time:
                #Premier packet à arriver dans la liste 
                i,j,t,delta = self.packets[0]
                #vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                while self.packets!=[] and t > self.time:
                    #vprint(f"The packet is not arrived yet, packet lost")
                    self.add_plot(i,j,t,1) #For plotting
                    newres = self.players[i].treated(0,j,self.time,self.mu)
                    self.update(i,j) #Replacing the packet
                    self.packets.pop(0)
                    #Updating reservation (can be done more efficiently)
                    for j in newres: 
                        if self.reservations[i][j] != newres[j][0]:
                            self.event_times.pop(self.event_times.index((self.reservations[i][j],1,i,j)))
                            self.reservations[i][j] = newres[j][0]
                            self.insert_event((newres[j][0],1,i,j))
                    if self.packets!=[]:
                        i,j,t,delta = self.packets[0]
                        #vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                if self.packets!=[]:
                    self.treatment = self.time+delta
                    self.insert_event((self.treatment,2,i,j))
                    #vprint(f"Processing... Remaining time: {delta}")  
        if self.treatment==self.time:
            # Paquet traité
            if self.packets!=[]:
                i,j,t,delta = self.packets.pop(0)
                #vprint(f"Packet ({i},{j}) treated.")
                self.treatment = -1
                self.add_plot(i,j,t,0) 
                newres = self.players[i].treated(1,j,self.time,self.mu) # Inform the player his packet have been treated
                self.update(i,j)
                #Updating reservation (can be done more efficiently)
                for j in newres: 
                    if self.reservations[i][j] != newres[j][0]:
                        self.event_times.pop(self.event_times.index((self.reservations[i][j],1,i,j)))
                        self.reservations[i][j] = newres[j][0]
                        self.insert_event((newres[j][0],1,i,j))
                # Prise en charge d'un nouveau packet
                if self.packets!=[]:
                    i,j,t,delta = self.packets[0]
                    #vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                    while self.packets!=[] and t > self.time:
                        #vprint(f"The packet is not arrived yet, packet lost")
                        self.add_plot(i,j,t,1)
                        newres = self.players[i].treated(0,j,self.time,self.mu)
                        self.update(i,j)
                        #Updating reservation (can be done more efficiently)
                        for j in newres: 
                            if self.reservations[i][j] != newres[j][0]:
                                self.event_times.pop(self.event_times.index((self.reservations[i][j],1,i,j)))
                                self.reservations[i][j] = newres[j][0]
                                self.insert_event((newres[j][0],1,i,j))
                        self.packets.pop(0)
                        if self.packets!=[]:
                            i,j,t,delta = self.packets[0]
                            #vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                    if self.packets!=[]:
                        self.treatment = self.time + delta
                        self.insert_event((self.treatment,2,i,j))
                        #vprint(f"Processing... Remaining time: {delta}")
                #if self.packets==[]:
                    #vprint("No more packet to process.")
            #else:
                #vprint("No packet in queue")
        self.trettt+=tt.time()-ttt

    def game(self,plot=False,duration=100000):
        self.totttt = tt.time()
        i=0
        if self.new:
            f = open("data.txt",mode='w')
            f.write("ArTime\tResTime\tRetTime\tP\tAdv\tL\n")
            f.close()
        self.new = False
        if self.use_data:
            filename = str(self.mu) + "_"
            for i in range(self.n_players):
                filename += self.players[i].name + "_"
            if os.path.isfile("data/"+filename+str(duration)+"_"+str(self.seed)+".bin"):
                print("This simulation has already been done, and the data have been saved. Here are the results of that simulation. Be sure that the code has not changed since that last simulation")
                with open("data/"+filename+str(duration)+"_"+str(self.seed)+".bin","rb") as fp:
                    data = pickle.load(fp)
                self.time = data[0]
                self.times = data[1][0].tolist()
                self.tota = data[1][1].tolist()
                for i in range(self.n_players):
                    filename += self.players[i].name + "_"
                    self.y[i] = data[i+2][0]
                    self.players[i].processed = data[i+2][1]
                    self.players[i].total_loss = data[i+2][2]
                    self.players[i].total_waiting_time = data[i+2][3]
                    self.players[i].processed = data[i+2][4]
                    self.players[i].advance = data[i+2][5]
        while self.time<duration:
            ttt = tt.time()
            if self.time==-1:
                self.event = self.event_times.pop(0)
                self.time = self.event[0]
            if int(self.time/duration*20)>i:
                print(f"Execution : {int(self.time/duration*20)*5}%")
                print(f"N PACKETS : {len(self.packets)}")
                i = int(self.time/duration*20)
            #vprint(f"Time: {self.time}")
            ##vprint(f"Event times: {self.event_times}")
            #vprint(f"Remaining treatment time: {self.treatment-self.time}")
            #vprint(f"Packets: {self.packets}")
            ##vprint(f"Revelation Times: {self.revelation}")
            ##vprint(f"Arrival Times: {self.arrival_times}")
            ##vprint(f"Last Arrival {self.last_arrival}")
            ##vprint(f"Reservation Times: {self.reservations}")
            ##vprint(f"Player1 res times: {self.players[1].reservations}")
            #vprint("")
            self.othttt+= tt.time()-ttt
            self.turn()
            ttt = tt.time()
            self.times.append(self.time)
            self.tota.append(sum([self.players[i].advance for i in range(self.n_players)]))
            self.event = self.event_times.pop(0)
            self.time = self.event[0]
            #self.packetsinfile.append((self.time,len(self.packets))) #Pour tracer le nombre de packets dans la file
            #self.timeinfile.append((self.time,sum([e[3] for e in self.packets]))) #Pour tracer la courbe de l'attente dans la file
            #vprint(f"Waiting time in the file: {self.timeinfile[-1][1]}")
            #vprint("------")
            #if funs.stop:
                #input()
            self.othttt2 += tt.time()-ttt
        self.totttt = tt.time() - self.totttt
        print(f"\nTheoretical mean wait: {self.theoretical_wait}")
        print(f"Theoretical mean time in sys: {self.theoretical_time_in_sys}\n")
        #ppm.plt.plot([e[0] for e in self.timeinfile],[e[1] for e in self.timeinfile])
        #ppm.plt.plot([e[0] for e in self.packetsinfile],[e[1] for e in self.packetsinfile])
        if self.keep_data:
            filename = str(self.mu) + "_"
            filecontent = [duration,[np.array(self.times),np.array(self.tota)]]
            for i in range(self.n_players):
                filename += self.players[i].name + "_"
                filecontent.append([self.y[i],self.players[i].processed,self.players[i].total_loss,self.players[i].total_waiting_time,self.players[i].processed,self.players[i].advance])
            with open("data/"+filename+str(duration)+"_"+str(self.seed)+".bin","wb") as fp:
                pickle.dump(filecontent,fp)
        if plot:
            ppm.plotTime(np.array(self.times),np.array(self.tota),"Total Advance")
        for i in range(self.n_players):
            if plot:
                #ppm.plotXY(np.array(self.y[i][0]),np.array(self.y[i][1]),np.array(self.y[i][2]),f"Player{i}_({self.players[i].name})")
                ppm.plotXYTime(np.array(self.y[i][3]),np.array(self.y[i][0]),np.array(self.y[i][1]),np.array(self.y[i][2]),f"Player{i}_({self.players[i].name})",'png')
            print(f"Player {i+1} ({self.players[i].name}):\n - Total packets processed: {self.players[i].processed}\n - Total packets lost: {self.players[i].total_loss}\n - Total waiting time: {self.players[i].total_waiting_time}\n - Mean waiting time: {self.players[i].total_waiting_time/self.players[i].processed}\n - Final advance: {self.players[i].advance}\n")
        print(f"TTT:\n - Revelation: {self.revttt}s\n - Reservation: {self.resttt}s\n - Treatment: {self.trettt}s\n - Insertion: {self.insttt}s\n - Others: {self.othttt}s\n - Others2: {self.othttt2}s\n - Total: {self.totttt}s") 
        if self.n_players>1:
            scorep0 = funs.evalperf(self.theoretical_time_in_sys,self.players[0].processed,self.players[0].total_waiting_time,self.players[0].total_loss)
            scorep1 = funs.evalperf(self.theoretical_time_in_sys,self.players[1].processed,self.players[1].total_waiting_time,self.players[1].total_loss)
            return ((self.players[0].processed,self.players[0].total_waiting_time/self.players[0].processed,self.players[0].advance,scorep0,self.players[0].processed/(self.players[0].processed+self.players[0].total_loss)),(self.players[1].processed,self.players[1].total_waiting_time/self.players[1].processed,self.players[1].advance,scorep1,self.players[1].processed/(self.players[1].processed+self.players[1].total_loss)))
        return 0

def simu(alpha_init,alpha_end,step_alpha,beta_init,beta_end,step_beta,duration):
    lbda = 5
    alpharange = np.arange(alpha_init,alpha_end,step_alpha)
    betarange = np.arange(beta_init,beta_end,step_beta)
    results = {}
    for beta in betarange:
        print(beta)
        for alpha in alpharange:
            print(' ',alpha)
            careful = players.CarefulPlayer()
            alphabeta = players.AlphaBetaConst(alpha,beta)
            #simu
            for mu in np.arange(3.5,4.5,0.5):
                g = Game([careful,alphabeta,careful,careful,careful,careful,careful,careful,careful,careful,careful],lbda,500,mu)
                results[(mu,alpha,beta)] = g.game(False,duration)
                print(results[(mu,alpha,beta)][0][3]," ",results[(mu,alpha,beta)][1][3])
                if results[(mu,alpha,beta)][0][3]>results[(mu,alpha,beta)][1][3]:
                    print("WOOOOOOOOOOOOOW",mu,alpha,beta)
    return results