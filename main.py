import players
import numpy as np
import functions as funs
from functions import vprint
from copy import deepcopy

class Game:

    def insert_event(self,event_time):
        """
        @brief: Inserts an event in the sorted list of events
        @param event_time: The time of the event to insert
        @return: None
        """
        if self.time != event_time:
            self.event_times.append(10000000000)
            tmp1 = event_time
            tmp2 = 0
            place_founded = False
            i = 0
            while i < len(self.event_times):
                if (not place_founded) and event_time <= self.event_times[i]:
                    place_founded = True
                if place_founded and event_time == self.event_times[i]:
                    self.event_times.pop(-1)
                    break
                if place_founded:
                    tmp2 = self.event_times[i]
                    self.event_times[i] = tmp1
                    tmp1 = tmp2
                i+=1

    def __init__(self,players,lbda,initial_size=100,mu=0):
        self.initial_size = initial_size #The number of packets already created
        self.players = deepcopy(players) #The list of players playing the game
        self.n_players = len(players) #The number of players
        self.lbda = lbda #The lambda of the game (mean arrival time for the players)
        self.event_times = [] #The list of times of next happening events (sorted)
        self.time = -1 #The time of the game
        if mu==0:
            self.mu = sum([self.players[i].lbda for i in range(self.n_players)])/self.n_players/self.n_players #The mu of the game
        else:
            self.mu = mu #The mean treatment times of the packets
        def initialisation(n_players,lbda,initial_size=100):
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
                    revelation = max(0,time-nu*np.random.random())
                    ari[j] = time
                    revi[j] = revelation
                    self.insert_event(time)
                    self.insert_event(revelation)
                ar.append(ari)
                rev.append(revi)
            return ar,rev
        ar,rev = initialisation(self.n_players,lbda,initial_size)
        self.arrival_times = ar #List of the lists of the first 'initial_size' arrival times for all players
        self.last_arrival = [max(self.arrival_times[i].values()) for i in range(self.n_players)] #List of the last arrival time for each player (not to look for the max at every update)
        self.revelation = rev #List of the lists of the first 'initial_size' revelation times for all players
        self.reservations = [{} for j in range(self.n_players)] #List of the lists of the first 'initial_size' reservation times for all players (-1 if no reservation yet)
        for j in range(self.n_players):
            for i in range(initial_size):
                self.reservations[j][i] = -1
        self.packets = [] #The file of packets to treat (i,j,t,delta) for player i packet j, arriv time t, treatment time delta
        self.treatment = -1 #The remaining treatement time

    def update(self,player_i,packet_id):
        """
        @brief: Updates the packets for player i, after one of his packets was treated, so his list of packets remains full 
        @param player_i: The player whose list of packets must be updated 
        @param packet_id: The id of the processed packet in the dictionnaries
        @return: None
        """
        nu = self.players[player_i].nu
        time = self.last_arrival[player_i] + np.random.exponential(self.lbda)
        self.insert_event(time)
        self.last_arrival[player_i] = time 
        self.arrival_times[player_i][packet_id] = time
        self.revelation[player_i][packet_id] = max(self.time+0.01,time-nu*np.random.random())
        self.insert_event(self.revelation[player_i][packet_id])
        self.reservations[player_i][packet_id] = -1
    
    def turn(self):
        # Reavealing arrival time to clients
        for i in range(self.n_players):
            for j in self.revelation[i]:
                if self.revelation[i][j]==self.time:
                    vprint(f"Revealing arrival time ({self.arrival_times[i][j]}) of packet {j} to player {i} ({self.players[i].name}) at time {self.time}.")
                    res_time = self.players[i].reserve(self.time,self.arrival_times[i][j],j)
                    vprint(f"Player {i} ({self.players[i].name}) reserves at time {res_time} for packet {j} arriving at time {self.arrival_times[i][j]}.")
                    self.reservations[i][j] = res_time
                    self.insert_event(res_time)
        # Reserving a place in the queue
        for i in range(self.n_players):
            for j in self.reservations[i]:
                if self.reservations[i][j]==self.time:
                    vprint(f"Player {i} ({self.players[i].name}) reserved at time {self.time} for packet {j}.")
                    self.packets.append((i,j,self.arrival_times[i][j],np.random.exponential(self.mu)))
                    vprint(f"Adding packet {j} to packets queue...")
                    vprint(f"Queue state: {self.packets}")
        # Treating packets
        if self.packets!=[]:    
            if self.treatment<self.time:
                #Premier packet à arriver dans la liste 
                i,j,t,delta = self.packets[0]
                vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                while self.packets!=[] and t > self.time:
                    vprint(f"The packet is not arrived yet, packet lost")
                    self.players[i].treated(0,j,self.time,self.mu)
                    self.update(i,j) #Replacing the packet
                    self.packets.pop(0)
                    if self.packets!=[]:
                        i,j,t,delta = self.packets[0]
                        vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                if self.packets!=[]:
                    self.treatment = self.time+delta
                    self.insert_event(self.treatment)
                    vprint(f"Processing... Remaining time: {delta}")  
        if self.treatment==self.time:
            # Paquet traité
            if self.packets!=[]:
                i,j,t,delta = self.packets.pop(0)
                vprint(f"Packet ({i},{j}) treated.")
                self.players[i].treated(1,j,self.time,self.mu) # Inform the player his packet have been treated
                self.update(i,j)
                # Prise en charge d'un nouveau packet
                if self.packets!=[]:
                    i,j,t,delta = self.packets[0]
                    vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                    while self.packets!=[] and t > self.time:
                        vprint(f"The packet is not arrived yet, packet lost")
                        self.players[i].treated(0,j,self.time,self.mu)
                        self.update(i,j)
                        self.packets.pop(0)
                        if self.packets!=[]:
                            i,j,t,delta = self.packets[0]
                            vprint(f"Packet ({i},{j}) next in the file. Arrival time: {t}, current time: {self.time}")
                    if self.packets!=[]:
                        self.treatment = self.time + delta
                        self.insert_event(self.treatment)
                        vprint(f"Processing... Remaining time: {delta}")
                if self.packets==[]:
                    vprint("No more packet to process.")
            else:
                vprint("No packet in queue")

    def game(self,duration=100000):
        i=0
        while self.time<duration:
            if self.time==-1:
                self.time = self.event_times.pop(0)
            if int(self.time/duration*1000)/10>i:
                print(f"Execution : {int(self.time/duration*1000)/10}%")
                i = int(self.time/duration*1000)/10
            vprint(f"Time: {self.time}")
            vprint(f"Event times: {self.event_times}")
            vprint(f"Remaining treatment time: {self.treatment-self.time}")
            vprint(f"Packets: {self.packets}")
            vprint(f"Revelation Times: {self.revelation}")
            vprint(f"Arrival Times: {self.arrival_times}")
            vprint(f"Last Arrival {self.last_arrival}")
            vprint(f"Reservation Times: {self.reservations}")
            self.turn()
            self.time = self.event_times.pop(0)
            if funs.verb:
                input()
        for i in range(self.n_players):
            print(f"Player {i+1} ({self.players[i].name}):\n - Total packets processed: {self.players[i].processed}\n - Total packets lost: {self.players[i].total_loss}\n - Total waiting time: {self.players[i].total_waiting_time}\n - Final advance: {self.players[i].advance}\n")