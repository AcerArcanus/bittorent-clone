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
#might need threading to make multiple connections 
#peer prompts user to send file over to peer
#inputs: filename, port, IP, 

#create static IP and port variables
srcIP = "192.168.10.58"
srcPort = 5500

#creates socket that uses IPv4 and TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    #bind socket to IP and port
    s.bind((srcIP, srcPort))
    #connect to server using IP
    s.connect(("192.168.10.55", 8080))#server IP
    #then send a post request of all available files?
     

class peerComm:
    def __init__(self, srcIP, srcPort, fileName): #ip and port would likely be initialized earlier
        self.srcIP = srcIP
        self.srcPort = srcPort
        self.fileName = fileName

        #[insert socket creation code?]

    #sends file to client that requested file (this client was chosen because he has the best bandwith)
    def peerSend(self, destIP, destPort, fileName):
        sock.connect((destIP, destPort)) #connect to client
        try:
           # Reading file and sending data to client
            fi = open(fileName, "rb")
            data = fi.read(1024)
            while data:
                sock.sendall(data)
                data = fi.read(1024)
            # File is closed after data is sent
            fi.close()
            # error for when filename is not found
        except IOError:
            print('You entered an invalid filename!\
                Please enter a valid name')

  #receives file from peer post request
  def peerReceive(incIP, incPort):
      socket.connect((incIP, incPort)) #connects to the peer its expecting a file from
      #receives file and prints when entire file is received
      file = b" "
      while True:
        fileChunk = socket.recv(1024)
        if not fileChunk:
          print("File received:", file.decode('utf-8'))
          break
        file += fileChunk  

        
    #send a request to the peer that has the file with the best bandwith, 
    def sendPeerRequest(self):
        #take in list of devices that have desired file, pick the one with the best bandwith?
        #send a request to the chosen peer, prompting them to send the file back, send message with your port and ip
        #run peerReceive()
    
    """
    def sendPeerRequest(self, destIP, destPort):
        # ---------------------------------------------------------
        # This peer wants to request a file from another peer.
        #
        # destIP and destPort identify the peer that has the file.
        # srcIP and srcPort identify this peer.
        # ---------------------------------------------------------

        # Connect to the peer that has the requested file
        self.socket.connect((destIP, destPort))

        # Create a request containing:
        # - The name of the file we want
        # - Our IP address
        # - Our port number
        request = f"{self.fileName}|{self.srcIP}|{self.srcPort}"

        # Convert the request to bytes and send it to the peer
        self.socket.sendall(request.encode())

        # Close the connection used to send the request
        self.socket.close()

        # Receive the requested file from the peer
        self.peerReceive(destIP, destPort)  
    """


    def receivePeerRequest(self):
        #listen for requests to your socket
        #requests would give you parameters to run peerSend()
        #send file

        """
         def receivePeerRequest(self):
        
        # Bind this peer's socket to its IP address and port
        self.socket.bind((self.srcIP, self.srcPort))

        # Start listening for incoming peer requests
        self.socket.listen()

        print("Waiting for peer requests...")

        while True:

            # Accept a connection from another peer
            connection, address = self.socket.accept()

            # Receive the request and convert it from bytes to text
            request = connection.recv(1024).decode()

            # The request contains:
            # fileName | requesting peer IP | requesting peer port
            requestedFile, destIP, destPort = request.split("|")

            print("File requested:", requestedFile)
            print("Sending to:", destIP, destPort)

            # Close the connection used for the request
            connection.close()

            # Send the requested file to the requesting peer
            self.peerSend(
                destIP,
                int(destPort),
                requestedFile
            )
        
        
        
        """