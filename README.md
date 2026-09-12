# bittorent-clone
An implementation of a P2P file-sharing system as a class project, based on the design of BitTorrent.

# Project Layout/Design Structure

## What should it do application side?
user should:
- establish connection with server to receive list of available files for download (UI)
- user should be able to input desired file
- be able to upload files ready for transfer to server
- user should be given info to connect with device based on the file it needs
- establish connection with device (IP,port) given by server
- IMPORTANT: figure out how to transfer a file once TCP connection is established (FTP?) 
- How should we maintain lists of available items as well as currently connected devices

## What does the server do?
- Accepts connections from users
- Asks them for files they have ready to transfer
- Accepts and stores the files they have ready for transfer 
- Maintains a list of files from each connected device and keeps track of who has which files 
- Gives the user this list of files
- When user picks the file they want, gives the user IP and port of the device/devices that have this file
- Adds user to the list of devices who have that file

## Error Handling
Q:What happens upon failure to connect to server?
A:Throw an error, attempt to recconnect

Q:What happens when the client fails to connect to the device the file is stored on 
A:Retry to connect a few times, if connection continues to fail, go to the next device in the list
