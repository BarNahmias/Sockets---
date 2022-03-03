# Sockets-  Multiplayer chat 
![image](https://user-images.githubusercontent.com/92825016/156610717-b32e3143-06f4-4079-8d45-9a0bb54c5ba5.png)

# The purpose of the project

- Creating a multi-participant messaging system , based on TCP protocol.
- Allows you to download files reliably (fast UDP).





# srerver
    
    this class represent the server  in the room chat all client connecting to the server and 
    the server do all the work do send messages between them and download file and send them
    we implement a RDT protocol over udp to send file using selective repeat protocol logic  
   

## server function

- **init**

    this func create the tcp socket.

- **send_files**

    send file to client that asking to know which file exists in the server

- **three_way_handshake**

three way handshake protocol used to make udp more reliable 

    used the same logic as tcp three way handshake
    * first - server will get syn from client
    * second - server will send the client back ack/syn 
    * third - server will wait for client ack
    
- **close_connection**

function to close udp connection used four way handshake using tcp close connection logic

- **check_ack**
- 
    function to check the ack that came back from the client to the server for the packet the server send
    after we gettting ack the "nack list" that representing the packet that still didnt got ack will be updated
    and we will move in our send window 
    
- **find_start_end**
- 
    this function used to update our send window each time we packet and ack that we got for them we will call this 
    function to see if we need to ypdate our window too
    
- **liding_window **
    
    this function does all the work to send the file to the client
    
    we used all our helper function in this function 
    we send the packet to the client in this function along with the seq attached to the packet
    and after the iteration we will check the ack we got for the packets
    
- **update_buffer** 
 
     function to update the buffer we are going to used for sending the file to the client
     
- **udp_transfer_files** 

    this function started by thread to start the udp file transfer doing some checks if the client already connected
    if not allocate a available port for him and try to connect him with the client using three wat handshake function 
    and than call to the main function that will transfer the file
    
- **broadcast**

    this function send messages for all other client in the room when client will send a massage everyone in the room
    will get the messages using this function
    
- **send_users**

      this function will send to the client which asking for all other user name their nick name
      
- **sent_to_other_user**

    this function used to send a private massege from one client to another
    
- **handle_messages**

    this function used to handle all messages in the room and calling the right function for each client messages
    
- **receive**

    this function used to establish the first connection when client connect to the server
    we will keep the client data in our data structure and notify all user that this client connect to the room
    and start a thread fot this client to listen to his masseges
- **main**
 
      create object from server type.
      operate receive function 
      
   # client
   
        this class represent the client side in the room chat when client 
        connect to the room he can send messages to other client and ask from the server to download a file for him
        the connection for sending messages used by a tcp socket and the connction for download a file used by a
        reliable udp that used selective repeat protocol to deliver the files
    
    ## client function
    
    - **init**
    
    - **three_way_handshake**
    
    function for establish the first connection for the udp socket 
    this way we make the protocol more reliable
    
    -**find_start_end**
   
   this function used to find the index of the packet that we didnt yet got them from the server
    in that way we can move in our receiving window after knowing we got the packet
    
    
   - **lose_connection**
    
    this function used for closing the connection between the client and the server
    after the client got all the segments from the server
    
    - **udp_handler**

    this function doing all the work to transfer the file
    * first checks if the client already connect by udp connection 
    * second bind the udp socket to the correct ip and port if not connect already
    * third calling to three way handshake function if necessary 
    * fifth receive the file and calling to close connection function

- **client_receive**

function that run by thread that used to receive messages from the client and display them to client screen

- **client_conncet**

    function to connect the client to the server by tcp connection
    and starting the threads that receive and send messages
    
    
-    **client_send**
        function to send the message to the server meaning to the room chat
        
- **main**        
        

# Schematic diagram of sending a message 

![image](https://user-images.githubusercontent.com/92825016/156647716-d92f616c-2d6d-46c5-83a6-234d394f2fd5.png)

 ![image](https://user-images.githubusercontent.com/92825016/156647842-c928952e-628c-4c92-ae0b-51a5222aadc2.png)


