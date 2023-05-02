from _thread import start_new_thread
import socket
import pickle
import math

import network

def parse_client_data(connection_socket: socket) -> network.Request:
    try:
        return pickle.loads(connection_socket.recv(network.MAX_DATA_SIZE))
    except ConnectionResetError or ConnectionAbortedError:
        print("Client process exited")
    except Exception as exception:
        print(f"Client {connection_socket.getpeername()} ran into unusual exception of type: {type(exception).__name__}")
    
    return None

def is_session_maintained(data, session_id: int, connection_socket: socket) -> bool:
    if data == None:
        pass
    elif session_id not in sessions:
        connection_socket.send(pickle.dumps(network.GameState(flags = [network.Flag(network.RESPONSE_SESSION_CLOSED, network.SESSION_NO_LONGER_EXISTS)])))
    else:
        return True
    
    print(f"Client {connection_socket.getpeername()} has disconnected unexpectedly")
    return False

def handle_client(connection_socket: socket, client_id: int, session_id: int):
    global client_indices_used

    connection_socket.send(str.encode(str(client_id)))

    while True:
        data = parse_client_data(connection_socket)
        if not is_session_maintained(data, session_id, connection_socket):
            break

        sessions[session_id] = network.handle_data(sessions[session_id], data, client_id)
        if isinstance(sessions[session_id], network.Flag):
            if sessions[session_id].command == network.REQUEST_DISCONNECT:
                print(f"Client {connection_socket.getpeername()} has disconnect: {sessions[session_id].details}")
            
            print(f"Session {session_id} has concluded: {sessions[session_id].details}")
            break
        
        connection_socket.send(pickle.dumps(sessions[session_id]))
        # print(f"Sent game state to client {client_id} in session {session_id}")

        sessions[session_id].flag_lists[client_id] = []

    connection_socket.close()
    try:
        del sessions[session_id]
        print(f"Session {session_id} deleted")
        client_indices_used = network.CLIENTS_PER_SESSION * math.ceil(client_indices_used / network.CLIENTS_PER_SESSION)
    except KeyError:
        print(f"Session {session_id} was already deleted")

def main():
    global client_indices_used

    connection_socket, remote_address = local_socket.accept()
    print("Connected to", remote_address)

    client_id = client_indices_used % network.CLIENTS_PER_SESSION
    session_id = client_indices_used // network.CLIENTS_PER_SESSION
    if client_id == 0:
        sessions[session_id] = network.GameState()
        print(f"Session {session_id} created")
    client_indices_used += 1

    start_new_thread(handle_client, (connection_socket, client_id, session_id))

if __name__ == '__main__':
    local_socket = socket.socket()

    try:
        local_socket.bind(network.SERVER_ADDRESS)
    except socket.error as error:
        print("Error occurred binding server:", error)
        exit()

    local_socket.listen()
    print(f"Server online, waiting for clients...")

    sessions = {}
    client_indices_used = 0

    while True:
        main()