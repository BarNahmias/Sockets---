import math
import threading

from Client import Client
import socket
import time
import os
import sys


class Server:

    """""
    this class represent the server  in the room chat all client connecting to the server and 
    the server do all the work do send messages between them and download file and send them
    we implement a RDT protocol over udp to send file using selective repeat protocol logic  
    """""
    max_packet_size = 2**16
    time_out = 0.01 # time out for socket rcv
    fragment_size = 500 # size of reading bytes from file each time
    seq_max = 10 # base of sequence numer packet in the sending window
    window_size = 5 # window segment size
    time_start = time.time()

    def __init__(self) -> None:
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #tcp socket to first connection and sending message
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # this option make the port avilable after client disconnect
        self.server_sock_udp_map = {}
        self.clients_map = {}  # dict used for tcp client for each key(nick_name) we will get the client object
        self.buffer_data = {}  # used to keep the file data for transfer
        self.file_names = []  # keep the file in the list
        self.udp_stopped = {}
        self.client_ip = {}
        self.ports = [0 for i in range(0, 15)]  # port number that available

    """""
    send file to client that asking to know which file exists in the server
    """""
    def send_files(self, nick_name):
        self.clients_map.get(nick_name).client_sock.send(f'the file names is : {self.file_names}'.encode('utf-8'))

    """""
    three way handshake protocol used to make udp more reliable 
    used the same logic as tcp three way handshake
    * first - server will get syn from client
    * second - server will send the client back ack/syn 
    * third - server will wait for client ack
    """""
    def three_way_handshake(self, nick_name, syn):
        while True:
            try:
                self.server_sock_udp_map.get(nick_name)[2].settimeout(self.time_out)
                if not syn:
                    print(self.server_sock_udp_map.get(nick_name)[2])
                    message, _ = self.server_sock_udp_map.get(nick_name)[2].recvfrom(self.max_packet_size)
                if  message.decode('utf-8') == 'SYN' or syn:
                    syn = True
                    self.server_sock_udp_map.get(nick_name)[2].sendto('ACK'.encode('utf-8'),(self.client_ip.get(nick_name), self.server_sock_udp_map.get(nick_name)[0]))
                    ans, _ = self.server_sock_udp_map.get(nick_name)[2].recvfrom(self.max_packet_size)
                    if ans.decode('utf-8') == 'ACK':
                        self.server_sock_udp_map.get(nick_name)[2].settimeout(None)
                        return True
            except:
                continue

    """""
    function to check the ack that came back from the client to the server for the packet the server send
    after we gettting ack the "nack list" that representing the packet that still didnt got ack will be updated
    and we will move in our send window 
    """""
    def check_ack(self, nack, start_index, end_index, precent, nick_name):
        while True:
            try:
                ack, _ = self.server_sock_udp_map.get(nick_name)[2].recvfrom(self.max_packet_size)
                to_send = 'SIZE:' + str((len(nack)-1))
                if ack.decode('utf-8') == 'SEND_SIZE':
                    self.server_sock_udp_map.get(nick_name)[2].sendto(to_send.encode('utf-8'),(self.client_ip.get(nick_name), self.server_sock_udp_map.get(nick_name)[0]))
                for i in range(start_index, end_index):
                    if i % 10 == int(ack.decode('utf-8')) % 10:
                        print(f'got ack for packet number {i}')
                        nack[i] = 1
            except :
                break

    """""
    this function used to update our send window each time we packet and ack that we got for them we will call this 
    function to see if we need to ypdate our window too
    """""
    def find_start_end(self, nack):
        for i in range(0, len(nack)):
            if nack[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(nack)-1)
                return start_index, end_index

    """""
    this function does all the work to send the file to the client 
    we used all our helper function in this function 
    we send the packet to the client in this function along with the seq attached to the packet
    and after the iteration we will check the ack we got for the packets
    """""
    def sliding_window(self, nick_name, file_name):
        start_index = 0
        end_index = 0
        finished = True
        precent = 0
        nack_packet = [0 for i in range(0, len(self.buffer_data.get(nick_name).get(file_name)))]
        packet_number_help_me = 0
        bool_precent = True
        len(self.buffer_data.get(nick_name).get(file_name))
        to_send = 'SIZE:' + str(len(nack_packet)-1)
        self.server_sock_udp_map.get(nick_name)[2].sendto(to_send.encode('utf-8'), (self.client_ip.get(nick_name), self.server_sock_udp_map.get(nick_name)[0]))
        while end_index <= len(nack_packet):
            print(self.udp_stopped.get(nick_name))
            for i in range(len(nack_packet)-self.window_size, len(nack_packet)):
                if nack_packet[i] == 0:
                    finished = False
            if finished:
                break
            if self.udp_stopped.get(nick_name) is None:
                end_index = len(nack_packet)+1
                break
            start_index, end_index = self.find_start_end(nack_packet)
            print(start_index,end_index)
            if start_index == 0 and end_index == 0:
                break
            if start_index==end_index and start_index == len(nack_packet)-1:
                data = self.buffer_data.get(nick_name).get(file_name)[start_index]
                ind = (start_index % self.seq_max).to_bytes(1, byteorder='big')
                packet = ind+data
                self.server_sock_udp_map.get(nick_name)[2].sendto(packet, (self.client_ip.get(nick_name), self.server_sock_udp_map.get(nick_name)[0]))
                self.check_ack(nack_packet, start_index, end_index, precent, nick_name)
            for k in range(start_index, end_index):
                if nack_packet[k] == 0:
                    data = self.buffer_data.get(nick_name).get(file_name)[k]
                    ind = (k % self.seq_max).to_bytes(1, byteorder='big')
                    packet_number_help_me += 1
                    packet = ind+data
                    self.server_sock_udp_map.get(nick_name)[2].sendto(packet, (self.client_ip.get(nick_name), self.server_sock_udp_map.get(nick_name)[0]))
            precent = (start_index / len(nack_packet)) * 100
            self.server_sock_udp_map.get(nick_name)[2].settimeout(self.time_out)
            precent = "{:.2f}".format(precent)
            self.check_ack(nack_packet, start_index, end_index, precent, nick_name)
            if bool_precent and float(precent) > 40:
                bool_precent = False
                sent_once = False
                while True:
                    self.server_sock_udp_map.get(nick_name)[2].settimeout(3)
                    try:
                        self.server_sock_udp_map.get(nick_name)[2].sendto('CONFIRM_PROCEED'.encode('utf-8'),(self.client_ip.get(nick_name), self.server_sock_udp_map.get(nick_name)[0]))
                        msg, _ = self.server_sock_udp_map.get(nick_name)[2].recvfrom(1024)
                        rmsg = msg.decode('utf-8').split(':')
                        if msg.decode('utf-8') == 'PROCEED':
                            self.server_sock_udp_map.get(nick_name)[2].settimeout(self.time_out)
                            break
                        elif msg.decode('utf-8') == 'NO_PROCEED':
                                end_index = len(nack_packet) + 1
                                break
                        else:
                            continue
                    except:
                        pass
        print(f'finished to transfer file to client {nick_name}')
    """""
    function to update the buffer we are going to used for sending the file to the client
    """""
    def update_buffer(self, nick_name, file_name, segment_size):
        with open(file_name, 'rb') as f:
            j = 0
            while j <= segment_size:
                data = f.read(self.fragment_size)
                self.buffer_data.get(nick_name).get(file_name).append(data)
                j+=1
    """""
    this function started by thread to start the udp file transfer doing some checks if the client already connected
    if not allocate a available port for him and try to connect him with the client using three wat handshake function 
    and than call to the main function that will transfer the file
    """""
    def udp_transfer_files(self, nick_name, file_name):
        bol = False
        bol_2 = True
        file_size = os.path.getsize(file_name)
        segment_size = math.ceil(file_size/self.fragment_size)
        if self.buffer_data.get(nick_name) is None:
            self.buffer_data[nick_name] = {}
            self.buffer_data.get(nick_name)[file_name] = []
            self.udp_stopped[nick_name] = 0

            print(self.udp_stopped.get(nick_name),nick_name)
        if self.buffer_data.get(nick_name) is not None:
            if self.buffer_data.get(nick_name).get(file_name) is None:
                self.buffer_data.get(nick_name)[file_name] = []
        if self.server_sock_udp_map.get(nick_name) is None:
            port_to_listen = 0
            port_to_send = 0
            j = 0
            first = True
            for i in range(0, 15):
                if self.ports[i] == 0 and first:
                    j = i
                    port_to_listen = self.ports[i]
                    self.ports[i] = 1
                    first = False
                if self.ports[i] == 0:
                    port_to_send = self.ports[i]
                    bol = True
                    self.ports[i] = 1
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(('127.0.0.1', 55003 + i))
                    self.server_sock_udp_map[nick_name] = (55003 + j, 55003 + i, sock)
                    self.sent_to_other_user(nick_name, f'listen to port {self.server_sock_udp_map.get(nick_name)}'.encode('utf-8'))
                    break
        else:
            self.sent_to_other_user(nick_name, f'listen to port {self.server_sock_udp_map.get(nick_name)}'.encode('utf-8'))
        if bol:
            bol_2 = self.three_way_handshake(nick_name, False)
            bol = bol_2
        if bol_2 or bol:
            self.update_buffer(nick_name, file_name, segment_size)
            self.sliding_window(nick_name, file_name)

    """""
    this function send messages for all other client in the room when client will send a massage everyone in the room
    will get the messages using this function 
    """""
    def broadcast(self, message, nick_name):
        for nick, client in self.clients_map.items():
            if nick != nick_name:
                client.client_sock.send(message)

    """""
    this function will send to the client which asking for all other user name their nick name
    """""
    def send_users(self, nick_name):
        list_to_send = []
        for nick in self.clients_map:
            if nick != nick_name:
                list_to_send.append(nick)
        self.clients_map[nick_name].client_sock.send(f'the cliens names is : {list_to_send}'.encode('utf-8'))
        
    """""
    this function used to send a private massege from one client to another
    """""
    def sent_to_other_user(self, receiver, message_to):
        self.clients_map.get(receiver).client_sock.send(message_to)

    """""
    this function used to handle all messages in the room and calling the right function for each client messages
    """""
    def handle_messages(self, nick_name):
        while True:
            try:
                message = self.clients_map[nick_name].client_sock.recv(1024).decode('utf-8')
                if message == f'{nick_name}: disconnect':
                    self.broadcast(f'{nick_name} has left the chat room'.encode('utf-8'), nick_name)
                    self.clients_map.get(nick_name).client_sock.send('Goodbye'.encode('utf-8'))
                    self.clients_map.pop(nick_name)
                    if self.server_sock_udp_map.get(nick_name) is not None:
                        self.ports[self.server_sock_udp_map.get(nick_name)[0]-55003] = 0
                        self.ports[self.server_sock_udp_map.get(nick_name)[1] - 55003] = 0
                        self.buffer_data.pop(nick_name)
                        self.server_sock_udp_map.pop(nick_name)
                    break
                pure_message = message.split(": ")
                file_message = message.split(" ")
                send_to_message = str(pure_message).split("_")
                if len(file_message) >= 3 and file_message[1] == "download_file":
                        file_name = file_message[2]
                        if file_name in self.file_names:
                            download_thread = threading.Thread(target=self.udp_transfer_files, args=(nick_name, file_name))
                            download_thread .start()
                        else:
                            self.sent_to_other_user(nick_name, 'there is no such a file with that name'.encode('utf-8'))
                elif message == f'{nick_name}: get_file_names':
                    self.send_files(nick_name)
                elif pure_message[1] == "get_user_names":
                    self.send_users(nick_name)
                elif len(send_to_message) >= 3:
                    meta = send_to_message[0].split(",")
                    met_meta = meta[1][2:len(meta[1])]
                    if met_meta == "send" and send_to_message[1] == "to":
                        meta_revciver = send_to_message[2].split()
                        recever = meta_revciver[0]
                        print(recever)
                        if self.clients_map.get(recever) is not None:
                            message_to = '' + str(nick_name) + ":" + str(
                                send_to_message[2][len(recever):len(send_to_message[2]) - 2])
                            self.sent_to_other_user(recever, message_to.encode())
                        else:
                            self.sent_to_other_user(nick_name, f'{recever} isnt in the room anymore'.encode('utf-8'))
                elif message == f'{nick_name}: DONE':
                    self.udp_stopped.pop(nick_name)
                elif self.clients_map.get(nick_name) is not None:
                    self.broadcast(message.encode('utf-8'), nick_name)
            except:
                self.clients_map[nick_name].close()
                self.clients_map.pop(nick_name)
                break

    """""
    this function used to establish the first connection when client connect to the server
    we will keep the client data in our data structure and notify all user that this client connect to the room
    and start a thread fot this client to listen to his masseges
    """""
    def receive(self):
        while True:
            print('Server is running and listening')
            client, adress = self.server_sock.accept()
            new_client = Client()
            new_client.client_sock = client
            print(f'connection esatblish with {str(adress[0])}')

            client.send('nick?'.encode('utf-8'))
            nick_name = client.recv(1024).decode('utf-8')
            while self.clients_map.get(nick_name) is not None:
                client.send('choose another nick'.encode('utf-8'))
                nick_name = client.recv(1024).decode('utf-8')
                print(nick_name)
            new_client.nick_name = nick_name
            self.clients_map[nick_name] = new_client
            self.client_ip[nick_name] = adress[0]
            print(f'The nick_name of this client is {nick_name}')
            self.broadcast(f'{nick_name} has connected to the room'.encode('utf-8'), nick_name)
            client.send('you are connected'.encode('utf-8'))
            print(nick_name)
            tread = threading.Thread(target=self.handle_messages, args=(nick_name,))
            tread.start()


if __name__ == "__main__":
    server = Server()
    ip_chose = input("choose an ip to connect  ((press 1 for local ip)) -------- ((press 2 for the machine ip)) : ")
    if ip_chose == '1':
        server.server_sock.bind(('127.0.0.1',55000))
        server.server_sock.listen(5)
    if ip_chose == '2':
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        ip = sock.getsockname()[0]
        server.server_sock.bind(('ip', 55000))
        server.server_sock.listen(5)
        sock.close()
    server.file_names.append("test.txt")
    server.file_names.append("Mp4file.mp4")
    server.file_names.append("image.jpeg")
    server.file_names.append("another.txt")
    server.receive()
