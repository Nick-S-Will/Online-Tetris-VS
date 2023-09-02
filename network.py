import random

import game

SERVER_ADDRESS = ("34.130.84.251", 55555)

# Data inherent to specific type of game
CLIENTS_PER_SESSION = 2
MAX_DATA_SIZE = 4096

# Client request commands
REQUEST_SEND_LINES = "send"
REQUEST_GAME_OVER = "game over"
REQUEST_DISCONNECT = "dc"
# Request details
END_LOSE = "Lost"
EXIT_GAME = "Client properly exited game"
request_detail_lookup = {
    REQUEST_GAME_OVER: END_LOSE,
    REQUEST_DISCONNECT: EXIT_GAME
}

# Server response commands
RESPONSE_WAIT = "wait"
RESPONSE_ADD_LINES = "add"
RESPONSE_GAME_WON = "end"
RESPONSE_SESSION_CLOSED = "exit"
# Response details
WAITING_FOR_OPPONENT = "Waiting for a second player to join"
END_WIN = "Won"
SESSION_NO_LONGER_EXISTS = "Current session no longer exists"
response_detail_lookup = {
    RESPONSE_WAIT: WAITING_FOR_OPPONENT,
    RESPONSE_GAME_WON: END_WIN,
    RESPONSE_SESSION_CLOSED: SESSION_NO_LONGER_EXISTS
}

request_response_lookup = {
    REQUEST_SEND_LINES: RESPONSE_ADD_LINES,
    REQUEST_GAME_OVER: RESPONSE_GAME_WON,
    REQUEST_DISCONNECT: RESPONSE_SESSION_CLOSED
}

class Flag:
    def __init__(self, command: str, details):
        self.command = command
        self.details = details
    
    def __str__(self) -> str:
        return f"({self.command}, {self.details})"
    
    def __repr__(self):
        return str(self)

class Request:
    def __init__(self, board: game.Board, flags: list[Flag]):
        self.board = board
        self.flags = flags
    
    def __str__(self) -> str:
        return f"Board: ({self.board}) Flags: {self.flags}"

class GameState:
    def __init__(self, boards: list[game.Board] = None, flags: list[list[Flag]] = None, seed: int = random.random()):
        self.boards = CLIENTS_PER_SESSION * [game.Board.empty()] if boards == None else boards
        self.flag_lists = CLIENTS_PER_SESSION * [[]] if flags == None else flags
        self.seed = seed
    
    def __str__(self) -> str:
        return f"Boards:\n{self.boards}\nFlags:\n{self.flag_lists}"

def is_session_waiting(boards: list[game.Board]) -> bool:
    for board in boards:
        if board.falling_piece.color == '':
            return True

def get_responses(client_request: Request, client_id: int) -> list[Flag]:
    responses = []
    for request_flag in client_request.flags:
        response_command = request_response_lookup[request_flag.command]
        response_details = response_detail_lookup.get(response_command, request_flag.details)

        responses.append(Flag(response_command, response_details))
    
    return responses

def handle_data(server_state: GameState, client_request: Request, client_id: int) -> GameState | Flag:
    flag_lists = server_state.flag_lists

    for request_flag in client_request.flags:
        if request_flag.command == REQUEST_DISCONNECT:
            return request_flag
    
    boards = server_state.boards
    boards[client_id] = client_request.board
    if is_session_waiting(boards):
        flag_lists[client_id].append(Flag(RESPONSE_WAIT, WAITING_FOR_OPPONENT))

    responses = get_responses(client_request, client_id)
    
    if len(responses) > 0:
        for i in range(CLIENTS_PER_SESSION):
            if i == client_id:
                continue
            
            flag_lists[i].extend(responses)
    
    return GameState(boards, flag_lists, server_state.seed)