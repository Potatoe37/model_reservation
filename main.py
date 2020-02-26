import players
import functions as funs
import plotparam as ppm
from functions import vprint

from copy import deepcopy
import numpy as np
import bisect
import time as tt

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
        ttt = tt.time()
        self.event_times.append((10000000000,3,10000,10000))
        tmp1 = event
        tmp2 = 0
        place_founded = False
        i = 0
        while i < len(self.event_times):
            if (not place_founded) and event <= self.event_times[i]:
                place_founded = True
                if event == self.event_times[i]:
                    self.event_times.pop(-1)
                    ValueError("Impossible to insert event, already in list")
                    break
            if place_founded:
                tmp2 = self.event_times[i]
                self.event_times[i] = tmp1
                tmp1 = tmp2
            i+=1
        self.insttt += tt.time()-ttt

    def __init__(self,players,lbda,initial_size=50,mu=0):
        """
        @brief: Initialisation of the game
        @param players: list of participationg players
        @param lbda: the parameter lambda of all players (mean time between two packets arrival)
        @param initial_size: how far the game is anticipated (default 50)
        @param mu: the parameter mu of the game (mean treatment time of a packet by the server) (default lbda/number of players)
        @return: Object Game
        """
        np.random.seed(0)
        self.new = True #The game haven't started yet
        self.initial_size = initial_size #The number of packets already created
        self.players = [deepcopy(p) for p in players]  #The list of players playing the game
        self.n_players = len(players) #The number of players
        self.lbda = lbda #The lambda of the game (mean arrival time for the players)
        if self.lbda!=0:
            #Same lambda for every player
            for p in self.players:
                p.lbda = lbda
        self.event_times = [] #The list of times of next happening events (sorted), and, event type (0: revelation, 1: reservation, 2: treatment), player concerned, packet concerned
        self.event = (0,0,-1,-1)
        self.time = -1 #The time of the game
        if mu==0:
            self.mu = sum([self.players[i].lbda for i in range(self.n_players)])/self.n_players/self.n_players #The mu of the game
        else:
            self.mu = mu #The mean treatment times of the packets
        print(f"mu={self.mu}")
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
                for j in range(initial_size):
                    time += np.random.exponential(self.lbda)
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

    def update(self,player_i,packet_id):
        """
        @brief: Updates the packets for player i, after one of his packets was treated, so his list of packets remains full 
        @param player_i: The player whose list of packets must be updated 
        @param packet_id: The id of the processed packet in the dictionnaries
        @return: None
        """
        nu = self.players[player_i].nu
        time = max(self.last_arrival[player_i],self.time) + np.random.exponential(self.lbda)
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
        f.write(f"{ar_time}\t{self.players[player_i].reservations[packet_id][0]}\t{self.time}\t{player_i}\t{self.players[player_i].advance}\t{loss}\n")
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
                    newres = self.players[i].treated(0,j,self.time,self.mu)
                    self.add_plot(i,j,t,1) #For plotting
                    self.update(i,j) #Replacing the packet
                    self.packets.pop(0)
                    for j in newres: #Updating reservation (can be done more efficiently)
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
                newres = self.players[i].treated(1,j,self.time,self.mu) # Inform the player his packet have been treated
                self.add_plot(i,j,t,0) 
                self.update(i,j)
                for j in newres: #Updating reservation (can be done more efficiently)
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
                        newres = self.players[i].treated(0,j,self.time,self.mu)
                        self.add_plot(i,j,t,1)
                        self.update(i,j)
                        for j in newres: #Updating reservation (can be done more efficiently)
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
            f.close()
        self.new = False
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
            #vprint(f"Event times: {self.event_times}")
            #vprint(f"Remaining treatment time: {self.treatment-self.time}")
            #vprint(f"Packets: {self.packets}")
            #vprint(f"Revelation Times: {self.revelation}")
            #vprint(f"Arrival Times: {self.arrival_times}")
            ##vprint(f"Last Arrival {self.last_arrival}")
            #vprint(f"Reservation Times: {self.reservations}")
            #vprint(f"Player1 res times: {self.players[1].reservations}")
            #vprint("")
            self.othttt+= tt.time()-ttt
            self.turn()
            ttt = tt.time()
            self.times.append(self.time)
            self.tota.append(sum([self.players[i].advance for i in range(self.n_players)]))
            self.event = self.event_times.pop(0)
            self.time = self.event[0]
            #vprint("------")
            #if funs.stop:
            #    input()
            self.othttt2 += tt.time()-ttt
        self.totttt = tt.time() - self.totttt
        if plot:
            ppm.plotTime(np.array(self.times),np.array(self.tota),"Total Advance")
        for i in range(self.n_players):
            if plot:
                #ppm.plotXY(np.array(self.y[i][0]),np.array(self.y[i][1]),np.array(self.y[i][2]),f"Player{i}_({self.players[i].name})")
                ppm.plotXYTime(np.array(self.y[i][3]),np.array(self.y[i][0]),np.array(self.y[i][1]),np.array(self.y[i][2]),f"Player{i}_({self.players[i].name})")
            print(f"Player {i+1} ({self.players[i].name}):\n - Total packets processed: {self.players[i].processed}\n - Total packets lost: {self.players[i].total_loss}\n - Total waiting time: {self.players[i].total_waiting_time}\n - Final advance: {self.players[i].advance}\n")
        print(f"TTT:\n - Revelation: {self.revttt}s\n - Reservation: {self.resttt}s\n - Treatment: {self.trettt}s\n - Insertion: {self.insttt}s\n - Others: {self.othttt}s\n - Others2: {self.othttt2}s\n - Total: {self.totttt}s") 