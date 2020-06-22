verb = True
stop = True

def vprint(s):
    if verb:
        print(s)

def evalperf(c,processed,total_waiting_time,total_loss):
    B = 0 #Cost of booking a packet
    C = c #Cost of losing a packet
    return (B*processed)+(C*total_loss)/(total_loss+processed)+total_waiting_time/processed