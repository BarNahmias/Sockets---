# Sockets---


# srerver
    
    this class represent the server  in the room chat all client connecting to the server and 
    the server do all the work do send messages between them and download file and send them
    we implement a RDT protocol over udp to send file using selective repeat protocol logic  
   

## server function

### init
    this func create the tcp socket.

### send_files 
    send file to client that asking to know which file exists in the server

### three_way_handshake
three way handshake protocol used to make udp more reliable 

    used the same logic as tcp three way handshake
    * first - server will get syn from client
    * second - server will send the client back ack/syn 
    * third - server will wait for client ack
    
### close_connection
function to close udp connection used four way handshake using tcp close connection logic
### check_ack
    function to check the ack that came back from the client to the server for the packet the server send
    after we gettting ack the "nack list" that representing the packet that still didnt got ack will be updated
    and we will move in our send window 
    
### find_start_end
    this function used to update our send window each time we packet and ack that we got for them we will call this 
    function to see if we need to ypdate our window too
    
### sliding_window    
    this function does all the work to send the file to the client
    
    we used all our helper function in this function 
    we send the packet to the client in this function along with the seq attached to the packet
    and after the iteration we will check the ack we got for the packets
    
 ### update_buffer
     function to update the buffer we are going to used for sending the file to the client
### udp_transfer_files
    this function started by thread to start the udp file transfer doing some checks if the client already connected
    if not allocate a available port for him and try to connect him with the client using three wat handshake function 
    and than call to the main function that will transfer the file
    
### broadcast

    this function send messages for all other client in the room when client will send a massage everyone in the room
    will get the messages using this function
    
### send_users
      this function will send to the client which asking for all other user name their nick name
      
### sent_to_other_user
    this function used to send a private massege from one client to another
    
###  handle_messages
    this function used to handle all messages in the room and calling the right function for each client messages
    
### receive
    this function used to establish the first connection when client connect to the server
    we will keep the client data in our data structure and notify all user that this client connect to the room
    and start a thread fot this client to listen to his masseges
 ### main 
        create object from server type.
        operate receive function 
