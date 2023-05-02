import socket
import pickle

import network

class Client:
    def __init__(self):
        self.local_socket = socket.socket()
        self.id = self.connect()
    
    def connect(self):
        try:
            self.local_socket.connect(network.SERVER_ADDRESS)
            print(f"Connected to {network.SERVER_ADDRESS}")
            return int(self.local_socket.recv(8).decode())
        except Exception as exception:
            print(f"Exception occured trying to connect to server {network.SERVER_ADDRESS}: {exception}")
            exit()
    
    def send_request(self, data: network.Request) -> network.GameState:
        try:
            self.local_socket.send(pickle.dumps(data))
            # print(f"Sent {data}")
            return pickle.loads(self.local_socket.recv(network.MAX_DATA_SIZE))
        except Exception as exception:
            print(f"Exception occured trying to send \"{data}\": {exception}")