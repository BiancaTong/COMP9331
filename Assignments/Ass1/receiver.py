# Written by Bianca Tong for comp9331 ass1

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
#####################################################  Preparing work  #####################################################################################

### Define the STP segment
class segments:
    def __init__(self,seq_value=0,ack=0,ack_value=0,syn=0,fin=0,data=''):
        self.SEQ_Value=seq_value
        self.ACK_Flag=ack
        self.ACK_Value=ack_value
        self.SYN_Flag=syn
        self.FIN_Flag=fin
        self.DATA=data

### Create a UDP socket
try:
    receiverSocket=socket(AF_INET, SOCK_DGRAM)
except:
    print("Failed to create receiver socket.")
    sys.exit()    

### Bind socket to host and port
receiverPort=int(sys.argv[1])
try:
    receiverSocket.bind(('',receiverPort))
except:
    print("Bind failed.")
    sys.exit()

### Create a Reiceiver_log file
receiver_log=open("Receiver_log.txt","w")

### Define some useful data to be recorded
data_sum=0                              # Amount of (original) Data Received (in bytes) do not include retransmitted data
segement_sum=0                          # Number of (original) Data Segments Received
dup_segement_sum=0                      # Number of duplicate segments received (if any)

########################################################  A three-way handshake   ##########################################################################

receiver_isn=99                                                         # initialise the sequence number of receiver
start_time=time.time()

### first hand
first_hand,senderAddress=receiverSocket.recvfrom(2048)
first_hand_decode=pickle.loads(first_hand)
curr=time.time()
timm=curr-start_time
receiver_log.writelines("rsv  {:.3f}  S {:5d} {:3d} {:5d}\n".format(timm*1000,first_hand_decode.SEQ_Value,len(first_hand_decode.DATA),first_hand_decode.ACK_Value))

### second hand
if(first_hand_decode.SYN_Flag==1):
    print("receive SYN")
    second_hand=segments(seq_value=receiver_isn,ack=1,ack_value=first_hand_decode.SEQ_Value+1,syn=1)
    second_hand_encode=pickle.dumps(second_hand)
    receiverSocket.sendto(second_hand_encode,(senderAddress))
    curr=time.time()
    timm=curr-start_time
    receiver_log.writelines("snd  {:.3f}  SA{:5d} {:3d} {:5d}\n".format(timm*1000,second_hand.SEQ_Value,len(second_hand.DATA),second_hand.ACK_Value))
    print("sending SYNACK")
else:
    print("Connection error!!")
    receiverSocket.close()

### third hand
third_hand,senderAddress=receiverSocket.recvfrom(2048)
third_hand_decode=pickle.loads(third_hand)
curr=time.time()
timm=curr-start_time
receiver_log.writelines("rsv  {:.3f}  S {:5d} {:3d} {:5d}\n".format(timm*1000,third_hand_decode.SEQ_Value,len(third_hand_decode.DATA),third_hand_decode.ACK_Value))
if(third_hand_decode.ACK_Flag==1):
    print("receive ACK")
    print("Connecting...")
else:
    print("Connection error!!")
    receiverSocket.close()

#####################################################   Receive data into a new file   #####################################################################

### create a new filr to write in
file_name=sys.argv[2]
f=open(file_name,"wb")

### waiting for the first segments
content,senderAddress=receiverSocket.recvfrom(2048)
content_decode=pickle.loads(content)
segement_sum+=1
data_sum+=len(content_decode.DATA)

### initialize some useful data
seq_num=third_hand_decode.ACK_Value                                  # inintialize the seqence number of receiver
correct_seq=third_hand_decode.SEQ_Value                              # the sequence number we needed next (correct order)
last_seq=[]                                                          # the sequence number that has been received
waiting_list=[]                                                      # an empty list to buffer the segments out of order

### update the file while the fin flag is 0
while(content_decode.FIN_Flag==0):
    curr=time.time()
    timm=curr-start_time
    print("receive:  seq:{} ack:{}".format(content_decode.SEQ_Value,content_decode.ACK_Value))
    receiver_log.writelines("rsv  {:.3f}  D {:5d} {:3d} {:5d}\n".format(timm*1000,content_decode.SEQ_Value,len(content_decode.DATA),content_decode.ACK_Value))

    ### if the seqence number is in correct order
    if(content_decode.SEQ_Value==correct_seq):
        f.write(content_decode.DATA.encode())
        correct_seq+=len(content_decode.DATA)
        
        ### to compute the dup seqement
        if(content_decode.SEQ_Value in last_seq):
            dup_segement_sum+=1
        else:
            last_seq.append(content_decode.SEQ_Value)
        
        i=0
        ### to check whether there are correct segments already been transferred
        while(i<len(waiting_list)):
            if(waiting_list[i].SEQ_Value==correct_seq):
                f.write(waiting_list[i].DATA.encode())
                correct_seq+=len(waiting_list[i].DATA)
                del waiting_list[i]
                i=i-1
            i+=1

    ### if the sequence number is not in correct order
    else:
        ### to compute the dup seqement
        if(content_decode.SEQ_Value in last_seq):
            dup_segement_sum+=1
        else:
            last_seq.append(content_decode.SEQ_Value)
        
        ### if there is no segments in waiting list, just append
        if(waiting_list==[]):
            waiting_list.append(content_decode)
        else:
            ### to insert the new content at a right position in waiting list
            for i in range(0,len(waiting_list)):
                if(waiting_list[i].SEQ_Value>content_decode.SEQ_Value):
                    waiting_list.insert(i,content_decode)
                    break
                if(i==len(waiting_list)-1):
                    waiting_list.append(content_decode)
                    break
    
    ### send the needed sequence number in ack value
    response=segments(seq_value=seq_num,ack=1,ack_value=correct_seq)
    response_encode=pickle.dumps(response)
    receiverSocket.sendto(response_encode,(senderAddress))
    curr=time.time()
    timm=curr-start_time
    receiver_log.writelines("snd  {:.3f}  A {:5d} {:3d} {:5d}\n".format(timm*1000,response.SEQ_Value,len(response.DATA),response.ACK_Value))
    print("send:     seq:{} ack:{}".format(response.SEQ_Value,response.ACK_Value))

    ### receive segments from sender
    content,senderAddress=receiverSocket.recvfrom(2048)
    content_decode=pickle.loads(content)
    segement_sum+=1
    data_sum+=len(content_decode.DATA)
print("File Download!")
    
##################################################    Four-segment connection termination    ###############################################################

### receive the fin flag
first_end=content
first_end_decode=pickle.loads(first_end)
if(first_end_decode.FIN_Flag==1):
    curr=time.time()
    timm=curr-start_time
    receiver_log.writelines("rsv  {:.3f}  F {:5d} {:3d} {:5d}\n".format(timm*1000,first_end_decode.SEQ_Value,len(first_end_decode.DATA),first_end_decode.ACK_Value))

    ### send the ack flag
    second_end=segments(seq_value=first_end_decode.ACK_Value,ack=1,ack_value=first_end_decode.SEQ_Value+1)
    second_end_encode=pickle.dumps(second_end)
    receiverSocket.sendto(second_end_encode,(senderAddress))
    print("ending...2")

    ### send the fin flag
    third_end=segments(seq_value=first_end_decode.ACK_Value,ack_value=first_end_decode.SEQ_Value+1,fin=1)
    third_end_encode=pickle.dumps(third_end)
    receiverSocket.sendto(third_end_encode,(senderAddress))
    curr=time.time()
    timm=curr-start_time
    receiver_log.writelines("snd  {:.3f}  FA{:5d} {:3d} {:5d}\n".format(timm*1000,third_end.SEQ_Value,len(third_end.DATA),third_end.ACK_Value))
    print("ending...3")

### receive the ack flag, then shut down
receiverSocket.settimeout(1)
try:
    forth_end,senderAddress=receiverSocket.recvfrom(2048)
    forth_end_decode=pickle.loads(forth_end)
    curr=time.time()
    timm=curr-start_time
    receiver_log.writelines("rsv  {:.3f}  A {:5d} {:3d} {:5d}\n".format(timm*1000,forth_end_decode.SEQ_Value,len(forth_end_decode.DATA),forth_end_decode.ACK_Value))
    if(forth_end_decode.ACK_Flag==1):
        receiverSocket.close()
        print("close receiver")
except timeout:
    curr=time.time()
    timm=curr-start_time
    receiver_log.writelines("rsv  {:.3f}  A {:5d} {:3d} {:5d}\n".format(timm*1000,first_end_decode.SEQ_Value+1,0,first_end_decode.ACK_Value+1))
    receiverSocket.close()
    print("close receiver")

f.seek(0,2)
receiver_log.writelines("Amount of (original) Data Received (in bytes) do not include retransmitted data: %d\n" %data_sum)
receiver_log.writelines("Number of (original) Data Segments Received: %d\n" %(segement_sum-1))
receiver_log.writelines("Number of duplicate segments received (if any): %d\n" %dup_segement_sum)
f.close()
receiver_log.close()


