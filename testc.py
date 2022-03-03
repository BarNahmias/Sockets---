import threading
import socket


"""""
this class represent the client side in the room chat when client 
connect to the room he can send messages to other client and ask from the server to download a file for him
the connection for sending messages used by a tcp socket and the connction for download a file used by a
reliable udp that used selective repeat protocol to deliver the files
"""""
class Client2(object):
    connected = True # this virable used for knowing if the client still connected or not
    connected_udp = False
    fragment_size = 500  # size of bytes we are reading from teh file
    window_size = 5 # size of segment we are transferring in our receive window
    max_seq_num = 10 # base of the sequence number og the packets
    already_connect_udp = False
    file_data = [] # buffer for the data we are receiving from the server
    local = '127.0.0.1' #local ip adress
    time_out = 0.001  # should do the calculation for the timeout in efficient way
    max_buffer_size = 2 ** 16
    locked = True

    def __init__(self, nick_name=0) -> None:
        self.nick_name = nick_name
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_sock_udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port_to_send = 0

    """""
    function for establish the first connection for the udp socket 
    this way we make the protocol more reliable
     
    """""
    def three_way_handshake(self):
        print(self.local, self.port_to_send)
        print(type(self.local), type(self.port_to_send))
        self.client_sock_udp.settimeout(self.time_out)

        while True:
            try:
                self.client_sock_udp.sendto('SYN'.encode('utf-8'), (self.local, self.port_to_send))
                print("before recived")
                message, adress = self.client_sock_udp.recvfrom(self.max_buffer_size)
                print("recevied")
                if message.decode('utf-8') == 'ACK':
                    self.client_sock_udp.sendto('ACK'.encode('utf-8'), (self.local, self.port_to_send))
                    self.client_sock_udp.settimeout(None)
                    print("client_connect")
                    return True
            except:
                continue
    """""
    this function used to find the index of the packet that we didnt yet got them from the server
    in that way we can move in our receiving window after knowing we got the packet
    """""
    def find_start_end(self, rcv_list):
        for i in range(0, len(rcv_list)):
            if rcv_list[i] == 0:
                start_index = i
                end_index = min(i + self.window_size, len(rcv_list))
                return start_index, end_index
        return 0, 0
    """""
    this function used for closing the connection between the client and the server
    after the client got all the segments from the server
    """""
    def close_connection(self):
        print("trying")
        try:
            self.client_sock_udp.settimeout(self.time_out)
            self.client_sock_udp.sendto('FIN'.encode('utf-8'), (self.local, self.port_to_send))
            print("C1 before acked")
            ans, _ = self.client_sock_udp.recvfrom(1024)
            if ans.decode('utf-8') == 'ACK':
                print("C1 after acked")
                self.close_connection_2()
                return
            else:
                print("C1 not acked")
                self.close_connection()
        except:
            print("C1 timeout")
            self.close_connection()
    """""
    this function used for closing the connection between the client and the server
    after the client got all the segments from the server
    """""
    def close_connection_2(self):
        try:
            self.client_sock_udp.settimeout(None)
            ans, _ = self.client_sock_udp.recvfrom(1024)
            print("C2 got ans ")
            while ans.decode('utf-8') != 'FIN':
                ans, _ = self.client_sock_udp.recvfrom(1024)
                print(ans.decode('utf-8'))
            self.client_sock_udp.settimeout(self.time_out * 2)
            while True:
                self.client_sock_udp.sendto('ACK'.encode('utf-8'), (self.local, self.port_to_send))
                print("inside")
                ans, _ = self.client_sock_udp.recvfrom(1024)
                print("inside2")
        except:
            return

    """""
    this function doing all the work to transfer the file
    * first checks if the client already connect by udp connection 
    * second bind the udp socket to the correct ip and port if not connect already
    * third calling to three way handshake function if necessary 
    * fifth receive the file and calling to close connection function
    """""
    def udp_handler(self, port_l):
        print("inside")
        bol = True
        finished = True
        start_index = 0
        end_index = 0
        if not self.connected_udp:
            self.client_sock_udp.bind(('127.0.0.1', port_l))
            bol = self.three_way_handshake()
        if bol:
            self.connected_udp = True
            real_message = ''
            message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            while real_message == 'ACK':
                try:
                    self.client_sock_udp.settimeout(self.time_out)
                    self.client_sock_udp.sendto('ACK'.encode('UTF-8'), (self.local, self.port_to_send))
                    message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
                    real_message = message.decode('utf-8')
                except:
                    continue
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            while real_message.split(':')[0] != 'SIZE':
                try:
                    self.client_sock_udp.settimeout(self.time_out)
                    self.client_sock_udp.sendto('SEND_SIZE'.encode('utf-8'), (self.local, self.port_to_send))
                    message, address = self.client_sock_udp.recvfrom(self.max_buffer_size)
                    real_message = message.decode('utf-8')
                except:
                    continue
            try:
                real_message = message.decode('utf-8')
            except:
                pass
            if real_message.split(':')[0] == 'SIZE':
                rcv_list = [0 for i in range(0, int(real_message.split(':')[1]))]
                buffer_list = [0 for i in range(0, int(real_message.split(':')[1]))]
            self.client_sock_udp.settimeout(None)
            bool_confirm = True
            user_input = None
            while end_index <= len(rcv_list):
                for i in range(len(rcv_list) - self.window_size, len(rcv_list)):
                    if rcv_list[i] == 0:
                        finished = False
                if finished:
                    break
                start_index, end_index = self.find_start_end(rcv_list)
                if start_index == 0 and end_index == 0:
                    break
                for k in range(start_index, end_index):
                    if k == len(rcv_list):
                        break
                    data, _ = self.client_sock_udp.recvfrom(1024)
                    decoded_data = ''
                    try:
                        decoded_data = data.decode('utf-8')
                    except:
                        pass
                    if decoded_data == 'SIZE':
                        self.client_sock_udp.sendto('ACK', (self.local, self.port_to_send))
                        continue
                    if decoded_data == 'CONFIRM_PROCEED':
                        print("shold confirm")
                        if user_input is None:
                            while user_input != 'yes' and user_input != 'no':
                                user_input = input("You downloaded 40% of the file, Do you want to proceed? [yes,no]")
                        if bool_confirm:
                            if user_input == 'yes':
                                self.client_sock_udp.sendto('PROCEED'.encode('utf-8'), (self.local, self.port_to_send))
                                continue
                            elif user_input == 'no':
                                self.client_sock_udp.sendto('NO_PROCEED'.encode('utf-8'), (self.local, self.port_to_send))
                                end_index = len(rcv_list) + 1
                                break
                        else:
                            if user_input == 'yes':
                                bool_confirm = True
                            elif user_input == 'no':
                                bool_confirm = True
                    seq_num = int.from_bytes(data[0:1], byteorder='big')
                    temp_start, temp_end = self.find_start_end(rcv_list)
                    temp = [i % 10 for i in range(temp_start, temp_end)]
                    if seq_num not in temp:
                        self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), (self.local, self.port_to_send))
                    else:
                        if rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] == 0:
                            buffer_list[(end_index - (end_index - seq_num) % self.max_seq_num)] = data[1:]
                            rcv_list[(end_index - (end_index - seq_num) % self.max_seq_num)] = 1
                            self.client_sock_udp.sendto(f'{seq_num}'.encode('utf-8'), (self.local, self.port_to_send))
                            temp_start += 1
                            temp_end += 1
            self.close_connection()
            print("closed connction should end")
            if user_input == 'yes':
                file_name = input("please enter a file name : ")
                while file_name.strip(' ') == '':
                    file_name = input("please enter a file name : ")
                file = open(file_name, 'wb')
                for i in buffer_list:
                    ty = type(i)
                    if str(ty) == "<class 'bytes'>":
                        file.write(i)
                    last_byte = buffer_list[len(rcv_list)-1][-1]
                print(f'User {self.nick_name} downloaded 100% out of the file, Last byte is : {last_byte}')
                print("Done")
            else:
                print("File transfer stopped by user.")

    def choose_nick_name(self):
        self.nick_name = input('choose a nick_name >>>')
    """""
    function that run by thread that used to receive messages from the client and display them to client screen
    """""
    def client_receive(self):
        while True:
            if not self.connected:
                break
            try:
                message = self.client_sock.recv(1024).decode('utf-8')
                if str(message) == f'{self.nick_name}: Goodbye':
                    print("Goodbye")
                    self.client_sock.close()
                    self.client_sock_udp.close()
                elif message == "nick?":
                    self.client_sock.send(self.nick_name.encode('utf-8'))
                elif message == 'choose another nick':
                    self.locked = False
                    self.nick_name = input('please choose another nick_name >>>')
                    self.client_sock.send(self.nick_name.encode('utf-8'))
                    self.locked = True
                elif len(message) >= 14 and message[0:14] == "listen to port":
                    port_num = (message[15:len(message)]).split(',')
                    port_l = port_num[0][1:len(port_num[0])]
                    port_s = port_num[1][1:len(port_num[1])]
                    print(port_l)
                    print(port_s)
                    self.port_to_send = int(port_s)
                    # print(type(port_num))
                    # print(int(port_l))
                    receive_udp_thread = threading.Thread(target=self.udp_handler, args=(int(port_l), ))
                    receive_udp_thread.start()
                else:
                    print(message)
            except:
                print('Error!')
                self.client_sock.close()
                exit(1)
                break
    """""
    function to connect the client to the server by tcp connection
    and starting the threads that receive and send messages
    """""
    def client_conncet(self):
        self.client_sock.connect(('127.0.0.1', 55000))
        receive_thread = threading.Thread(target=self.client_receive)
        receive_thread.start()
        send_thread = threading.Thread(target=self.client_send)
        send_thread.start()

    """""
    function to send the message to the server meaning to the room chat
    """""
    def client_send(self):
        while self.connected:
                c_input = input("")
                if self.locked:
                    message = f'{self.nick_name}: {c_input}'
                    self.client_sock.send(message.encode('utf-8'))
                    if c_input == "exit":
                        self.connected = False


if __name__ == '__main__':
    client = Client2()
    client.choose_nick_name()
    client.client_conncet()
