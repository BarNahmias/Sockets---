import unittest
from Client import Client
from Server import Server
import threading
import time


class SystemTest(unittest.TestCase):


    def test_connecting(self):
        server = Server()
        server.receive()
        client = Client()
        client.nick_name = "yarin"
        client.client_conncet()
        time.sleep(1)
        client.client_sock.send(f'{client.nick_name}: exit'.encode('utf-8'))
        print(client.connected)
        self.assertEqual(client.connected, False)

    def test_send_other_client(self):
        server = Server()
        server.receive()
        client1 = Client()
        client1.nick_name = "a"
        client1.client_conncet()
        time.sleep(1)
        client2 = Client()
        client2.nick_name = "b"
        client2.client_conncet()
        time.sleep(1)
        print(server.clients_map)

    def test_get_user_names(self):
        client1 = Client()
        client1.nick_name = "a"
        client1.client_conncet()
        time.sleep(1)
        client2 = Client()
        client2.nick_name = "b"
        client2.client_conncet()
        client2.client_sock.send(f'{client2.nick_name}: get_user_names'.encode('utf-8'))
        time.sleep(1)
        massage = client2.client_sock.recv(1024).decode()
        print(massage)
        self.assertEqual(massage, "the client name is (['a'])")

    def test_exit_from_room(self):
        client1 = Client()
        client1.nick_name = "a"
        client1.client_conncet()
        client2 = Client()
        client2.nick_name = "b"
        client2.client_conncet()
        client1.client_sock.send(f'{client1.nick_name}: exit'.encode('utf-8'))
        time.sleep(1)
        msg = client2.client_sock.recv(1024).decode()
        self.assertEqual(msg, "client a has left the chat")





