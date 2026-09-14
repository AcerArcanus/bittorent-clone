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
#continuosly check that file for changes and update the file as needed


#info from server 
#gives user a list of available files to download
#gives user a list of device(ports and IP's) that have that file

#peer request function?

#Peer Receive function
#user receives a request from another peer for a file they have
#receive filename, port, IP


#Peer Send function
#make a decision given list of available devices with desired file based on bandwith (list will be provided from elsewhere, ignore for now)
#might need threading to make multing connections 
#peer prompts user to send file over to peer
#inputs: filename, port, IP, 

class peerComm:
    def __init__(self, srcIP, srcPort, fileName): #ip and port would likely be initialized earlier
        self.srcIP = srcIP
        self.srcPort = srcPort
        self.fileName = fileName

        #[insert socket creation code]

    #the device with the best bandwith is passed through this function
    def peerSend(self, destIP, destPort, fileName):
        sock.connect((destIP, destPort))
        try:
           # Reading file and sending data to server
            fi = open(fileName, "r")
            data = fi.read()
            if not data:
                break
            while data:
                sock.send(str(data).encode())
                data = fi.read()
            # File is closed after data is sent
            fi.close()
        except IOError:
            print('You entered an invalid filename!\
                Please enter a valid name')