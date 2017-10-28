# Written by Bianca Tong for comp9331 ass1 in 1/09/2017 using python 3.5.3

# A file is to be transferred from the sender to receiver.
# Data segments will flow from the sender to receiver.
# ACK segments will flow from the receiver to sender.
from socket import *
from random import *
import threading
import pickle
import time
import sys
import os
######################################################   Define class and function   #######################################################################

### Define the STP segment
class segments:
    def __init__(self,seq_value=0,ack=0,ack_value=0,syn=0,fin=0,data=''):
        self.SEQ_Value=seq_value                   # sequence number
        self.ACK_Flag=ack                          # ack flag use to justify the ack segment
        self.ACK_Value=ack_value                   # ack value: the next sequence number
        self.SYN_Flag=syn                          # syn flag use to justify the syn segment: for the handshake
        self.FIN_Flag=fin                          # fin flag use to justify the fin segment: for the termination
        self.DATA=data                             # data: the content of the file

### Define the PLD module
def PLD(pdrop):
    rand=random()
    if(rand>pdrop):
        return True
    else:
        return False

#########################################################   Preparing work   ###############################################################################

### Create a UDP socket
try:
    senderSocket=socket(AF_INET, SOCK_DGRAM)
except:
    print("Failed to create receiver socket.")
    sys.exit()

### Get receiver host and port
receiverHost=sys.argv[1]
receiverPort=int(sys.argv[2])

### Get other limitation data
mws=int(sys.argv[4])
mss=int(sys.argv[5])
timeoutt=int(sys.argv[6])
pdrop=float(sys.argv[7])
seed_num=int(sys.argv[8])
seed(seed_num)

### Create a Sender_log file
sender_log=open("Sender_log.txt","w")

### Define some useful data to be recorded
trans_segements_num=0                              # Number of Data Segments Sent (excluding retransmissions)
packet_drop_num=0                                  # Number of (all) Packets Dropped  (by the PLD module)
retrans_segments_num=0                             # Number of Retransmitted Segments
dup_ack_num=0                                      # Number of Duplicate Acknowledgements received

confirm_recv_flag=0                                # flag to confirm received ack
start_timer_flag=0                                 # flag to start timer
timeout_flag=0                                     # flag to justify timeout
close_flag=0                                       # flag to close receive thread

#########################################################  A three-way handshake  ##########################################################################

sender_isn=88                                       # initialise the sequence number of sender
start_time=time.time()
### first hand
first_hand=segments(seq_value=sender_isn,syn=1)
first_hand_encode=pickle.dumps(first_hand)
senderSocket.sendto(first_hand_encode,(receiverHost,receiverPort))
curr=time.time()
timm=(curr-start_time)*1000
sender_log.writelines("snd  {:.3f}  S {:5d} {:3d} {:5d}\n".format(timm,first_hand.SEQ_Value,len(first_hand.DATA),0))
print("sending SYN")

### second hand
second_hand,receiverAddress=senderSocket.recvfrom(2048)
second_hand_decode=pickle.loads(second_hand)
curr=time.time()
timm=(curr-start_time)*1000
sender_log.writelines("rsv  {:.3f}  SA{:5d} {:3d} {:5d}\n".format(timm,second_hand_decode.SEQ_Value,len(second_hand_decode.DATA),second_hand_decode.ACK_Value))

### third hand
if(second_hand_decode.SYN_Flag==1 and second_hand_decode.ACK_Flag==1):
    print("receive SYNACK")
    third_hand=segments(seq_value=sender_isn+1,ack=1,ack_value=second_hand_decode.SEQ_Value+1)
    third_hand_encode=pickle.dumps(third_hand)
    senderSocket.sendto(third_hand_encode,(receiverHost,receiverPort))
    curr=time.time()
    timm=(curr-start_time)*1000
    sender_log.writelines("snd  {:.3f}  A {:5d} {:3d} {:5d}\n".format(timm,third_hand.SEQ_Value,len(third_hand.DATA),third_hand.ACK_Value))
    print("sending ACK")
else:
    print("Connecting error!!")
    senderSocket.close()
    sys.exit()

#########################################################    Send all the file      ########################################################################

### initialize the useful data
seq_num=third_hand.SEQ_Value                        # initialize the sequence value of the first segment
ack_num=third_hand.ACK_Value                        # initialize the ack value of the first segment
sendbase=seq_num                                    # the sequence before sendbase is already received
ack_last=seq_num                                    # ack_last use for the newest ack segment received
data_in_window=0                                    # to match the mws

### Get the file and transfer it into segements list
file_name=sys.argv[3]
f=open(file_name,"rb")
ff=os.stat(file_name)
i=0
file_segements=[]
seq_num_num=seq_num
while(i<ff.st_size):
    f.seek(i)
    content=f.read(mss)
    data=segments(seq_value=seq_num_num,ack_value=ack_num,data=content.decode())
    file_segements.append(data)
    seq_num_num+=mss
    i+=mss
    if(i<ff.st_size and i+mss>=ff.st_size):
        f.seek(i)
        content=f.read(ff.st_size-i)
        data=segments(seq_value=seq_num_num,ack_value=ack_num,data=content.decode())
        file_segements.append(data)
        seq_num_num+=ff.st_size-i
        break

### Define the sender threading
senderSocket.settimeout(timeoutt/1000)
class sender_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        
        global ack_last
        global seq_num
        global sendbase
        global start_timer_flag
        global start_time
        global trans_segements_num
        global packet_drop_num
        global confirm_recv_flag
        global timeout_flag
        global retrans_segments_num
        global timer
        global stop_time
        
        i=0
        while(True):
            
            ### transfer data in the window
            while(seq_num-sendbase<=mws and i<len(file_segements)):
                data_encode=pickle.dumps(file_segements[i])
                if((seq_num+len(file_segements[i].DATA)-sendbase)>mws):
                    break
                ### PLD module to drop segments
                results=PLD(pdrop)
                if(results):
                    senderSocket.sendto(data_encode,(receiverHost,receiverPort))
                    
                    ### if timer does not start, start it
                    if(start_timer_flag==0):
                        timer=time.time()
                        start_timer_flag=1
                    
                    curr=time.time()
                    timm=(curr-start_time)*1000
                    sender_log.writelines("snd  {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm,file_segements[i].SEQ_Value,len(file_segements[i].DATA),file_segements[i].ACK_Value))
                    print("send:     seq:{} ack:{}".format(file_segements[i].SEQ_Value,file_segements[i].ACK_Value))
                    trans_segements_num+=1
                else:
                    ### if timer does not start, start it
                    if(start_timer_flag==0):
                        timer=time.time()
                        start_timer_flag=1
                    
                    curr=time.time()
                    timm=(curr-start_time)*1000
                    sender_log.writelines("drop {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm,file_segements[i].SEQ_Value,len(file_segements[i].DATA),file_segements[i].ACK_Value))
                    print("drop:     seq:{} ack:{}".format(file_segements[i].SEQ_Value,file_segements[i].ACK_Value))
                    trans_segements_num+=1
                    packet_drop_num+=1
                seq_num+=len(file_segements[i].DATA)
                i+=1
            
            ### to judge the timeout flag or received flag
            while(True):
                if(confirm_recv_flag==1 or timeout_flag==1):
                    #start_timer_flag=0
                    timeout_flag=0
                    break
                
                ### although the socket does not time out, we need to compute the timeout of segments receive ack
                stop_time=time.time()
                if((stop_time-timer)>=timeoutt/1000):
                    confirm_recv_flag=0
                    break
            
            ### if timeout then retransfer the segments
            if(confirm_recv_flag==0):
                m=int((ack_last-third_hand.SEQ_Value)/mss)
                data_encode=pickle.dumps(file_segements[m])
                results=PLD(pdrop)
                if(results):
                    senderSocket.sendto(data_encode,(receiverHost,receiverPort))
                    
                    ### start timer
                    timer=time.time()
                    start_timer_flag=1
                    
                    curr=time.time()
                    timm=(curr-start_time)*1000
                    sender_log.writelines("snd  {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm,file_segements[m].SEQ_Value,len(file_segements[m].DATA),file_segements[m].ACK_Value))
                    print("send:     seq:{} ack:{}".format(file_segements[m].SEQ_Value,file_segements[m].ACK_Value))
                    retrans_segments_num+=1
                else:
                    ### start timer
                    timer=time.time()
                    start_timer_flag=1
                    
                    curr=time.time()
                    timm=(curr-start_time)*1000
                    sender_log.writelines("drop {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm,file_segements[m].SEQ_Value,len(file_segements[m].DATA),file_segements[m].ACK_Value))
                    print("drop:     seq:{} ack:{}".format(file_segements[m].SEQ_Value,file_segements[m].ACK_Value))
                    retrans_segments_num+=1
                    packet_drop_num+=1
                continue
            
            ### if receive the correct response then continue
            confirm_recv_flag=0
            if(mss==mws):
                start_timer_flag=0
            ### if at the end of the file then break
            if(close_flag==1):
                break

### Define the receiver threading
class receiver_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global start_timer_flag
        global timeout_flag
        global close_flag
        global confirm_recv_flag
        global seq_num
        global ack_last
        global sendbase
        global dup_ack_num
        global trans_segements_num
        global packet_drop_num
        global retrans_segments_num
        global timer
        global start_time
        
        x=0
        while(True):
            ### if the timer is working
            if(start_timer_flag==1):
                try:
                    response,receiverAddress=senderSocket.recvfrom(2048)
                    response_decode=pickle.loads(response)
                    if(response_decode.ACK_Flag==1):
                        
                        ### change the last received ack value, which equal to the next needed sequence number
                        ack_last=response_decode.ACK_Value
                        curr=time.time()
                        timm=(curr-start_time)*1000
                        sender_log.writelines("rsv  {:.3f}  A {:5d} {:3d} {:5d}\n".format(timm,response_decode.SEQ_Value,len(response_decode.DATA),response_decode.ACK_Value))
                        print("receive:  seq:{} ack:{}".format(response_decode.SEQ_Value,response_decode.ACK_Value))
                        
                        ### if received a bigger ack, which means we received all of the segments before this ack, change the sendbase
                        if(response_decode.ACK_Value>sendbase):
                            x=1
                            sendbase=response_decode.ACK_Value
                            
                            ### change the flag of received
                            confirm_recv_flag=1
                            
                            ### if there exists unacked segments, start timer
                            if(seq_num!=sendbase):
                                timer=time.time()
                                start_timer_flag=1
                        else:
                            ### if received same ack number three times, then retransfer the segments
                            if(response_decode.ACK_Value==sendbase):
                                x+=1
                                dup_ack_num+=1
                                if(x>=3):
                                    x=0
                                    
                                    ### using the last received ack value to find the correct segments we want to send
                                    m=int((ack_last-third_hand.SEQ_Value)/mss)
                                    data_encode=pickle.dumps(file_segements[m])
                                    results=PLD(pdrop)
                                    if(results):
                                        senderSocket.sendto(data_encode,(receiverHost,receiverPort))
                                        timer=time.time()
                                        
                                        ### start timer
                                        start_timer_flag=1
                                        curr=time.time()
                                        
                                        timm=(curr-start_time)*1000
                                        sender_log.writelines("snd  {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm,file_segements[m].SEQ_Value,len(file_segements[m].DATA),file_segements[m].ACK_Value))
                                        print("send:     seq:{} ack:{}".format(file_segements[m].SEQ_Value,file_segements[m].ACK_Value))
                                        retrans_segments_num+=1
                                    else:
                                        ### start timer
                                        timer=time.time()
                                        start_timer_flag=1
                                        
                                        curr=time.time()
                                        timm=(curr-start_time)*1000
                                        sender_log.writelines("drop {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm,file_segements[m].SEQ_Value,len(file_segements[m].DATA),file_segements[m].ACK_Value))
                                        print("drop:     seq:{} ack:{}".format(file_segements[m].SEQ_Value,file_segements[m].ACK_Value))
                                        retrans_segments_num+=1
                                        packet_drop_num+=1
                                    #timeout_flag=1
                            else:
                                x=0
                        
                        ### if at the end of the file, break
                        if(response_decode.ACK_Value>=third_hand.SEQ_Value+ff.st_size):
                            close_flag=1
                            break
                ### if there is no received response, wait for timeout
                except timeout:
                    
                    ### if there is already a timer working, we just need to wait it
                    if(start_timer_flag==1):
                        continue
                    
                    ### if no timer working and the socket timeout, return timeout flag and restransfer the segment
                    timeout_flag=1
                    continue

### thread working(normal format)
threads=[]
thread1=sender_thread()
thread2=receiver_thread()
thread1.start()
thread2.start()
threads.append(thread1)
threads.append(thread2)
for t in threads:
    t.join()

#################################################   Four-segment connection termination   ##################################################################

### if at the end of the file
if(close_flag==1):
    
    ### send fin flag
    first_end=segments(seq_value=third_hand.SEQ_Value+ff.st_size,ack_value=ack_num,fin=1)
    first_end_encode=pickle.dumps(first_end)
    senderSocket.sendto(first_end_encode,(receiverHost,receiverPort))
    curr=time.time()
    timm=(curr-start_time)*1000
    sender_log.writelines("snd  {:.3f}  F {:5d} {:3d} {:5d}\n".format(timm,first_end.SEQ_Value,len(first_end.DATA),first_end.ACK_Value))
    print("ending...1")
    while(True):
        try:
            ### receive ack flag
            second_end,receiverAddress=senderSocket.recvfrom(2048)
            second_end_decode=pickle.loads(second_end)
            if(second_end_decode):
                break
        except timeout:
            continue
    if(second_end_decode.ACK_Flag==1):
        while(True):
            try:
        ### receive fin flag
                third_end,receiverAddress=senderSocket.recvfrom(2048)
                third_end_decode=pickle.loads(third_end)
                if(third_end_decode):
                    break
            except timeout:
                continue
        #if(third_end_decode.FIN_Flag==1):
        curr=time.time()
        timm=(curr-start_time)*1000
        sender_log.writelines("rsv  {:.3f}  FA{:5d} {:3d} {:5d}\n".format(timm,third_end_decode.SEQ_Value,len(third_end_decode.DATA),third_end_decode.ACK_Value))

        ### send ack flag
        forth_end=segments(seq_value=third_end_decode.ACK_Value,ack=1,ack_value=third_end_decode.SEQ_Value+1)
        forth_end_encode=pickle.dumps(forth_end)
        senderSocket.sendto(forth_end_encode,(receiverHost,receiverPort))
        curr=time.time()
        timm=(curr-start_time)*1000
        sender_log.writelines("snd  {:.3f}  A {:5d} {:3d} {:5d}\n".format(timm,forth_end.SEQ_Value,len(forth_end.DATA),forth_end.ACK_Value))
        print("close sender...")
        
        ### wait for a timeout, then shut down
        time.sleep(timeoutt/1000)
        senderSocket.close()
        sender_log.writelines("Amount of (original) Data Transferred (in bytes): %d\n" %ff.st_size)
        sender_log.writelines("Number of Data Segments Sent (excluding retransmissions): %d\n" %trans_segements_num)
        sender_log.writelines("Number of (all) Packets Dropped (by the PLD module): %d\n" %packet_drop_num)
        sender_log.writelines("Number of Retransmitted Segments: %d\n" %retrans_segments_num)
        sender_log.writelines("Number of Duplicate Acknowledgements received: %d\n" %dup_ack_num)
        f.close
        sender_log.close
