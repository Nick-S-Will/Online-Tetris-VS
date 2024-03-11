import socket
import pickle

import network

class Client:
    def __init__(self, address = network.SERVER_ADDRESS):
        self.local_socket = socket.socket()
        self.id = self.connect(address)
    
    def connect(self, address):
        try:
            self.local_socket.connect(address)
            print(f"Connected to {address}")
            return int(self.local_socket.recv(8).decode())
        except Exception as exception:
            print(f"Exception occured trying to connect to server {address}: {exception}")
    
    def send_request(self, data: network.Request) -> network.GameState:
        try:
            self.local_socket.send(pickle.dumps(data))
            # print(f"Sent {data}")
            return pickle.loads(self.local_socket.recv(network.MAX_DATA_SIZE))
        except Exception as exception:
            print(f"Exception occured trying to send \"{data}\": {exception}")