'''Author: Michael Giancola
 *Date: 22/11/2019
 *Description: This file contains a UDP Client application using the reliable data transfer protocol (rdt 3.0)
 to communicate across a network to a UDP Server that can corrupt or lose packets.
'''

import socket                                                   #includes all packages neccessary for application
import struct
import hashlib

UDP_IP = "127.0.0.1"                                            #the loopback adapter address; used to test communication on my local network
UDP_PORT = 5005                                                 #chosen allowable arbitrary port for communication
unpacker = struct.Struct('I I 8s 32s')                          #unpacker allows a packet later to be unpacked in the specified format

print("UDP target IP:", UDP_IP)                                 #print server address
print("UDP target port:", UDP_PORT)

#Create the UDP socket for the client
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

sock.settimeout(0.009)                                          #set the timeout value for the client socket to be 9ms

seq = 0                                                         #initialize the packet sequence number to zero

packets = ["NCC-1701", "NCC-1422", "NCC-1017"]                  #create a list of the packet data that is going to be sent to the server

for packet in packets:                                          #loop through the packet list above so that each one is sent to the server
    print("")
    values = (0,seq,packet.encode('utf-8'))                     #Create the Checksum using set sequence number and encode the data from the list
    UDP_Data = struct.Struct('I I 8s')                          #get the packet data stored in values and specify its packet format
    packed_data = UDP_Data.pack(*values)                        #pack the data
    chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")  #create a checksum using the packet data from the packet created

    #Build the UDP Packet
    values = (0,seq,packet.encode('utf-8'),chksum)
    UDP_Packet_Data = struct.Struct('I I 8s 32s')
    UDP_Packet = UDP_Packet_Data.pack(*values)

    #Send the UDP Packet to the server address specified above
    print("sent packet:", values)
    sock.sendto(UDP_Packet, (UDP_IP, UDP_PORT))

    while True:                                                             #infinite loop to ensure the packet has been received by the server intact
        try:                                                                #try to receive the acknowledgement packet set from the server withinn the set 9ms
            data, addr = sock.recvfrom(1024)                                #receive data, buffer size is 1024 bytes
            Ack_Packet = unpacker.unpack(data)                              #unpack the received ack packet data
            print("received from:", addr)
            print("received packet:", Ack_Packet)

            # create the checksum for comparison to check to see if the packet is corrupt
            ack_values = (Ack_Packet[0], Ack_Packet[1], Ack_Packet[2])
            packer = struct.Struct('I I 8s')
            packed_data = packer.pack(*ack_values)
            chksum = bytes(hashlib.md5(packed_data).hexdigest(), encoding="utf-8")

            # compare checksums to test for corrupt data
            if Ack_Packet[3] == chksum and Ack_Packet[0] == 1 and Ack_Packet[1] == seq:     #if the checksum matches the calculated checksum, the ack_is 1 and the correct seq # is recieved
                print("Ack packet not corrupt")
                seq = 1 - seq;                                                              #packet is received in tact and the client should now send data with the toggled sequence number
                break;                                                                      #break out of infinite loop and proceed to send the next data packet

            elif Ack_Packet[3] != chksum:                                                   #if the checksum does not equal the packets checksum then ack packet is corrupt
                print("Ack packet corrupt")

            else:                                                                           #else the packets sequence number is unexpected
                print("Unexpected sequence number")

        except socket.timeout:                                                              #if the correct ack packet does not reach the client within the timeout time of 9ms then resend the data packet to server
            print("timer expired")
            print("resending packet:", values)
            sock.sendto(UDP_Packet, (UDP_IP, UDP_PORT))




