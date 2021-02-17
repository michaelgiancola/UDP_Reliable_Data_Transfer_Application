'''Author: Michael Giancola
 *Date: 22/11/2019
 *Description: This file contains a UDP Server application using the reliable data transfer protocol (rdt 3.0)
 to communicate across a network that can corrupt or lose packets.
'''

import socket                                   #includes all packages neccessary for application
import struct
import hashlib
import time
import random

UDP_IP = "127.0.0.1"                            #the loopback adapter address; used to test communication on my local network
UDP_PORT = 5005                                 #chosen allowable arbitrary port for communication
unpacker = struct.Struct('I I 8s 32s')          #unpacker allows a packet later to be unpacked in the specified format

#this is the network delay function that causes an acknowledgement packet to be delayed around 33% of the time
def Network_Delay():
    if True and random.choice([0,1,0]) == 1:    #Set to False to disable Network Delay. Default is 33% packets are delayed
       time.sleep(.01)                          #delays the program for .01 seconds
       print("Packet Delayed")
    else:                                       #if not a delay
        print("Packet Sent")

#this is the network loss function that causes an acknowledgment packet to be lost and not received by client at all-lost 50% of time
def Network_Loss():
    if True and random.choice([0,1,1,0]) == 1:  #Set to False to disable Network Loss. Default is 50% packets are lost
        print("Packet Lost")
        return(1)
    else:                                       #if packet is not lost returns 0
        return(0)

#this is teh packet checksum corrupter that takes in the packet data and corrupts it 50% of the time
def Packet_Checksum_Corrupter(packetdata):
    if True and random.choice(
            [0, 1, 0, 1]) == 1:                 #Set to False to disable Packet Corruption. Default is 50% packets are corrupt
        return (b'Corrupt!')                    #returns corrupted data
    else:                                       #if data is not corrupted return packet data that was passed through originally
        return (packetdata)


#Create the UDP socket and listen
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

sock.bind((UDP_IP, UDP_PORT))                   #binds the port number 5005 to the server's socket

expected_seq = 0;                               #originally sets the expected sequence number to 0 which will be used by server and changed accordingly

while True:                                     #infinite loop which allows UDP Server to receive and process packets from clients continously
    print("")
    data, addr = sock.recvfrom(1024)            #Receive Data from client, buffer size is 1024 bytes
    UDP_Packet = unpacker.unpack(data)          #unpack the data packet into the unpacker format specified above
    print("received from:", addr)               #print the address of the host that sent the packet (Client address)
    print("received message:", UDP_Packet)      #print the contents of the packet, all values

    #Create the Checksum for comparison
    values = (UDP_Packet[0],UDP_Packet[1],UDP_Packet[2])                        #sets the ack bit, seq #, and data packet to a variable values
    packer = struct.Struct('I I 8s')                                            #put data stored in values into a packet of specified format
    packed_data = packer.pack(*values)                                          #actually pack the data above into a packet
    chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")      #create a checksum using the packet data from the packet created

    #Compare Checksums to test for corrupt data
    if UDP_Packet[3] == chksum and UDP_Packet[1] == expected_seq:               #if the checksum evaluated from the received packet matches the packet's checksum and the correct expected seq #
        print('CheckSums Match and expected sequence number, Packet OK')

        #Create an acknowledgement packet and create the Checksum using set sequence number (same as above when packing values into a packet)
        ack_values = (1, expected_seq, b'AckPcket')
        Ack_Data = struct.Struct('I I 8s')
        packed_data = Ack_Data.pack(*ack_values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Build the Ack Packet Packet
        ack_values = (1, expected_seq, Packet_Checksum_Corrupter(b'AckPcket'), chksum)  #here we are created the ack packet and including its checksum
        Ack_Packet_Data = struct.Struct('I I 8s 32s')
        Ack_Packet = Ack_Packet_Data.pack(*ack_values)

        if Network_Loss() == 0:                 #call the network_loss function to see if a loss of the ack packet to be sent will occur and if not go inside the if
            Network_Delay()                     #call network_delay to see if a delay will occur when sending the ack packet to the client
            sock.sendto(Ack_Packet, addr)       #send the ack packet to the address that the intial packet was received from
            print("sent packet:", ack_values)

        expected_seq = 1 - expected_seq         #whether there is a delay, loss, or nothing wrong, toggle the sequence number since we have recieved the clients packet and are expecting the next one

    else:                                       #if the checksums do not match or if an unexpected sequence number is received, regardless send the same ack packet
        if UDP_Packet[3] != chksum:                             #if checksums do not match then the clients packet is corrupt
            print('Checksums Do Not Match, Packet Corrupt')

        else:                                                   #if the sequence number is unexpected then repeated packet received
            print('Checksums Match but unexpected sequence number')

        #Create the ack packet and create the Checksum using set sequence number
        ack_values = (1, 1 - expected_seq, b'AckPcket')
        Ack_Data = struct.Struct('I I 8s')
        packed_data = Ack_Data.pack(*ack_values)
        chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")

        # Build the Ack Packet
        ack_values = (1, 1 - expected_seq, b'AckPcket', chksum)
        Ack_Packet_Data = struct.Struct('I I 8s 32s')
        Ack_Packet = Ack_Packet_Data.pack(*ack_values)

        # Send the UDP Packet to the address linked with the packet that was initially received
        sock.sendto(Ack_Packet, addr)
        print("sent packet:", ack_values)











