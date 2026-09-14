#code used to establish tcp connection
"""
import socket

#create static IP and port variables
statIP = "192.168.10.58"
port = 5500

#creates socket that uses IPv4 and TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #bind socket to IP and port
  #  s.bind((statIP, port))
    #connect to server using IP
    s.connect(("192.168.10.55", 8080))#self.destination)
    #sends http request
    s.sendall(b"yoyo")#req)    

"""

#request from server
#give server a folder of files you want available for transfer

#info from server 
#gives user a list of available files to download
#gives user a list of device(ports and IP's) that have that file


#Peer Receive function
#user receives a request from another peer for a file they have
#receive filename, port, IP


#Peer Send function
#might need threading to make multing connections 
#peer prompts user to send file over to peer
#inputs: filename, port, IP, 