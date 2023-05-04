import random
import copy

GRID_SIZE = 30
TILE_PADDING = 3
BOARD_TILE_WIDTH = 10
BOARD_TILE_HEIGHT = 20
WINDOW_PADDING = 10
BOARD_WIDTH = BOARD_TILE_WIDTH * GRID_SIZE
BOARD_HEIGHT = BOARD_TILE_HEIGHT * GRID_SIZE
SIDE_BAR_WIDTH = 5 * GRID_SIZE
PIECE_X_OFFSET = 3
MAX_FPS = 30

BASE_INPUT_MOVE_INTERVAL = 125
BASE_INPUT_TURN_INTERVAL = 250
BASE_UPDATE_INTERVAL = 300

class Piece:
        prefabs = [([(0, 0), (1, 0), (1, 1), (2, 1)], '#FF0000', 'Z'), # Red
                ([(0, 0), (1, 0), (2, 0), (0, 1)], '#FF7700', 'L'), # Orange
                ([(0, 0), (1, 0), (0, 1), (1, 1)], '#FFFF00', 'O'), # Yellow
                ([(2, 0), (1, 0), (0, 1), (1, 1)], '#00FF00', 'S'), # Green
                ([(0, 0), (1, 0), (2, 0), (3, 0)], '#00FFFF', 'I'), # Cyan
                ([(0, 0), (1, 0), (2, 0), (2, 1)], '#0000FF', 'J'), # Blue
                ([(0, 0), (1, 0), (2, 0), (1, 1)], '#DD00DD', 'T')] # Purple

        def __init__(self, prefab, has_offset = True):
            self.tiles, self.color, self.type = prefab
            if has_offset:
                self.tiles = [(PIECE_X_OFFSET + tile[0], tile[1]) for tile in self.tiles]
        
        def get_prefab(self):
            for prefab in Piece.prefabs:
                if self.type == prefab[2]:
                    return prefab

            return None
        
        def empty():
            return Piece(([], '', ''), False)
        
        def __str__(self) -> str:
            return f"Tiles: {self.tiles}, Color: {self.color}"

class Board:
    def __init__(self, ground_tiles: dict = None, falling_piece: Piece = None) -> None:
        self.ground_tiles = {} if ground_tiles == None else ground_tiles
        
        self.falling_piece = Piece(Piece.prefabs[random.randint(0, len(Piece.prefabs) - 1)]) if falling_piece == None else falling_piece

    def tile_is_invalid(self, tile):
        return tile in self.ground_tiles or tile[0] < 0 or BOARD_TILE_WIDTH <= tile[0] or tile[1] < 0 or BOARD_TILE_HEIGHT <= tile[1]

    def try_move_piece(self, piece: Piece, delta_x: int, delta_y: int):
        next_positions = []
        for tile in piece.tiles:
            next_positions.append((tile[0] + delta_x, tile[1] + delta_y))
            
            if self.tile_is_invalid(next_positions[-1]):
                return None
        
        return next_positions

    def try_turn_falling_piece(self, cw: bool):
        if self.falling_piece.type == 'O':
            return None
        
        direction = 1 if cw else -1
        next_positions = []
        rotation_index = 1
        for tile_index in range(len(self.falling_piece.tiles)):
            tiles = self.falling_piece.tiles

            position_delta = (tiles[tile_index][0] - tiles[rotation_index][0], tiles[tile_index][1] - tiles[rotation_index][1])
            next_positions.append((tiles[rotation_index][0] + (-1 * direction * position_delta[1]), tiles[rotation_index][1] + direction * position_delta[0]))

            if self.tile_is_invalid(next_positions[-1]):
                return None
        
        return next_positions
    
    def empty():
        return Board({}, Piece.empty())

    def __str__(self) -> str:
        return f"Ground: {self.ground_tiles} Piece: {self.falling_piece}"
    
    def __repr__(self) -> str:
        str(self)

class Game:
    def __init__(self, piece_type_seed: int = None) -> None:
        self.piece_type_randomizer = random.Random(random.random() if piece_type_seed == None else piece_type_seed)

        self.piece_order = copy.deepcopy(Piece.prefabs)
        self.piece_type_randomizer.shuffle(self.piece_order) 
        self.next_piece_index = 0
        self.board = Board(falling_piece = self.get_next_piece())

        self.input_move_interval = BASE_INPUT_MOVE_INTERVAL
        self.input_turn_interval = BASE_INPUT_TURN_INTERVAL
        self.update_interval = BASE_UPDATE_INTERVAL
        self.time_since_update = 0
        
        self.held_piece_prefab = None
        self.have_held = False
        self.alive = True
    
    def update_piece_index(self):
        self.next_piece_index = (self.next_piece_index + 1) % len(self.piece_order)

        if self.next_piece_index == 0:
            self.piece_type_randomizer.shuffle(self.piece_order)
    
    def get_next_piece(self) -> Piece:
        piece = Piece(self.piece_order[self.next_piece_index])
        self.update_piece_index()

        return piece
        
    def lift_all_tiles(self, amount: int):
        for y in range(BOARD_TILE_HEIGHT):
            target_y = y - amount

            for x in range(BOARD_TILE_WIDTH):
                try:
                    color = self.board.ground_tiles[(x, y)]
                    del self.board.ground_tiles[(x, y)]

                    if target_y < 0:
                        self.alive = False
                    else:
                        self.board.ground_tiles[(x, target_y)] = color
                except KeyError:
                    pass

    def add_lines(self, line_count: int = 1, tile_color = '#7F7F7F'):
        self.lift_all_tiles(line_count)
        
        for y in range(BOARD_TILE_HEIGHT - line_count, BOARD_TILE_HEIGHT):
            random_x = random.randint(0, BOARD_TILE_WIDTH - 1)

            for x in range(BOARD_TILE_WIDTH):
                if x == random_x:
                    continue

                self.board.ground_tiles[(x, y)] = tile_color

    def clear_lines(self, y_levels: list[int]):
        def get_row_to_move(last_moved_row) -> int:
            for y in range(last_moved_row - 1, -1, -1):
                if y not in y_levels:
                    return y

            return BOARD_TILE_HEIGHT

        last_moved_row = max(y_levels)
        for y in range(last_moved_row, 0, -1):
            row_to_move = get_row_to_move(last_moved_row)
            if row_to_move == BOARD_TILE_HEIGHT:
                break

            empty_tiles_in_line = 0
            for x in range(BOARD_TILE_WIDTH):
                tile_to_move_position = (x, row_to_move)

                if tile_to_move_position in self.board.ground_tiles:
                    self.board.ground_tiles[(x, y)] = self.board.ground_tiles[tile_to_move_position]
                    del self.board.ground_tiles[tile_to_move_position]
                else:
                    if (x, y) in self.board.ground_tiles:
                        del self.board.ground_tiles[(x, y)]
                    empty_tiles_in_line += 1

            if empty_tiles_in_line == BOARD_TILE_WIDTH:
                break

            last_moved_row = row_to_move

    def check_for_full_lines(self, y_levels: list[int]):
        full_line_y_levels = []
        for y in y_levels:
            full_line_y_levels.append(y)

            for x in range(BOARD_TILE_WIDTH):
                if (x, y) not in self.board.ground_tiles:
                    full_line_y_levels.remove(y)
                    break
        
        if len(full_line_y_levels) > 0:
            self.clear_lines(full_line_y_levels)
        
        return len(full_line_y_levels)
    
    def try_hold_falling_piece(self):
        if self.have_held:
            return

        if self.held_piece_prefab == None:
            self.held_piece_prefab = self.board.falling_piece.get_prefab()
            self.board.falling_piece = self.get_next_piece()
        else:
            temp = self.board.falling_piece.get_prefab()
            self.board.falling_piece = Piece(self.held_piece_prefab)
            self.held_piece_prefab = temp
        
        self.time_since_update = 0
        self.have_held = True

    def slam_falling_piece(self):
        self.input_move_interval = 2 ** 30
        self.input_turn_interval = self.input_move_interval
        self.update_interval = BASE_UPDATE_INTERVAL / 10
    
    def place_falling_piece(self):
        y_levels = []
        for tile in self.board.falling_piece.tiles:
            self.board.ground_tiles[tile] = self.board.falling_piece.color
            
            if tile[1] not in y_levels:
                y_levels.append(tile[1])
        
        self.board.falling_piece = self.get_next_piece()
        for tile in self.board.falling_piece.tiles:
            if tile in self.board.ground_tiles:
                self.alive = False
                return 0
        
        self.have_held = False
        self.input_move_interval = BASE_INPUT_MOVE_INTERVAL
        self.input_turn_interval = BASE_INPUT_TURN_INTERVAL
        self.update_interval = BASE_UPDATE_INTERVAL

        return self.check_for_full_lines(y_levels)

    def try_apply_gravity(self) -> int:
        next_positions = self.board.try_move_piece(self.board.falling_piece, 0, 1)
        if next_positions == None:
            return self.place_falling_piece()
        else:
            self.board.falling_piece.tiles = next_positions
            return 0