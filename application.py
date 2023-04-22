import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import random

import pygame_utilities

#region Constants
GRID_SIZE = 30
TILE_PADDING = 3
BOARD_TILE_WIDTH = 10
BOARD_TILE_HEIGHT = 20
WINDOW_PADDING = 10
BOARD_WIDTH = BOARD_TILE_WIDTH * GRID_SIZE
BOARD_HEIGHT = BOARD_TILE_HEIGHT * GRID_SIZE
SIDE_BAR_WIDTH = 5 * GRID_SIZE
PIECE_X_OFFSET = 3
MAX_FPS = 50

INPUTS_LEFT = [pygame.K_LEFT, pygame.K_a]
INPUTS_RIGHT = [pygame.K_RIGHT, pygame.K_d]
INPUTS_UP = [pygame.K_UP, pygame.K_w]
INPUTS_DOWN = [pygame.K_DOWN, pygame.K_s]
INPUTS_CCW = [pygame.K_z, pygame.K_COMMA]
INPUTS_CW = [pygame.K_x, pygame.K_PERIOD]
INPUTS_HOLD = [pygame.K_c, pygame.K_SLASH]

BASE_INPUT_MOVE_INTERVAL = 125
BASE_INPUT_TURN_INTERVAL = 250
BASE_UPDATE_INTERVAL = 300
#endregion

class Piece:
    prefabs = [([(0, 0), (1, 0), (1, 1), (2, 1)], '#FF0000', 'Z'), # Red
               ([(0, 0), (1, 0), (2, 0), (0, 1)], '#FF7700', 'L'), # Orange
               ([(0, 0), (1, 0), (0, 1), (1, 1)], '#FFFF00', 'O'), # Yellow
               ([(2, 0), (1, 0), (0, 1), (1, 1)], '#00FF00', 'S'), # Green
               ([(0, 0), (1, 0), (2, 0), (3, 0)], '#00FFFF', 'I'), # Cyan
               ([(0, 0), (1, 0), (2, 0), (2, 1)], '#0000FF', 'J'), # Blue
               ([(0, 0), (1, 0), (2, 0), (1, 1)], '#DD00DD', 'T')] # Purple
    next_prefab_index = 0

    def __init__(self, prefab = ..., has_offset = True):
        if prefab == ...:
            prefab = Piece.prefabs[Piece.next_prefab_index]
            
            Piece.next_prefab_index = (Piece.next_prefab_index + 1) % len(Piece.prefabs)
            if Piece.next_prefab_index == 0:
                random.shuffle(Piece.prefabs)
            
        self.tiles, self.color, self.type = prefab
        if has_offset:
            self.tiles = [(PIECE_X_OFFSET + tile[0], tile[1]) for tile in self.tiles]
    
    def get_prefab(self):
        for prefab in Piece.prefabs:
            if self.type == prefab[2]:
                return prefab

        return None
    
    def get_next_piece_prefab():
        return list(Piece.prefabs[Piece.next_prefab_index])

#region Line handling
def clear_lines(y_levels: list[int]):
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

            if tile_to_move_position in ground_tiles:
                ground_tiles[(x, y)] = ground_tiles[tile_to_move_position]
                del ground_tiles[tile_to_move_position]
            else:
                if (x, y) in ground_tiles:
                    del ground_tiles[(x, y)]
                empty_tiles_in_line += 1

        if empty_tiles_in_line == BOARD_TILE_WIDTH:
            break

        last_moved_row = row_to_move

def check_for_full_lines(y_levels: list[int]):
    full_line_y_levels = []
    for y in y_levels:
        full_line_y_levels.append(y)

        for x in range(BOARD_TILE_WIDTH):
            if (x, y) not in ground_tiles:
                full_line_y_levels.remove(y)
                break
    
    if len(full_line_y_levels) > 0:
        clear_lines(full_line_y_levels)
    
    return len(full_line_y_levels)
#endregion

#region Piece movement
def tile_is_invalid(tile):
    return tile in ground_tiles or tile[0] < 0 or BOARD_TILE_WIDTH <= tile[0] or tile[1] < 0 or BOARD_TILE_HEIGHT <= tile[1]

def try_move_piece(piece: Piece, x: int, y: int):
    next_positions = []
    for tile in piece.tiles:
        next_positions.append((tile[0] + x, tile[1] + y))
        
        if tile_is_invalid(next_positions[-1]):
            return None
    
    return next_positions

def try_turn_falling_piece(cw: bool):
    if falling_piece.type == 'O':
        return None
    
    direction = 1 if cw else -1
    next_positions = []
    rotation_index = 1
    for tile_index in range(len(falling_piece.tiles)):
        tiles = falling_piece.tiles

        position_delta = (tiles[tile_index][0] - tiles[rotation_index][0], tiles[tile_index][1] - tiles[rotation_index][1])
        next_positions.append((tiles[rotation_index][0] + (-1 * direction * position_delta[1]), tiles[rotation_index][1] + direction * position_delta[0]))

        if tile_is_invalid(next_positions[-1]):
            return None
    
    return next_positions

def slam_falling_piece():
    global input_move_interval
    global input_turn_interval
    global update_interval

    input_move_interval = 2 ** 30
    input_turn_interval = input_move_interval
    update_interval = 500 / MAX_FPS

def try_hold_falling_piece():
    global falling_piece
    global held_piece_prefab
    global have_held
    global time_since_update

    if have_held:
        return

    if held_piece_prefab == None:
        held_piece_prefab = falling_piece.get_prefab()
        falling_piece = Piece()
    else:
        temp = falling_piece.get_prefab()
        falling_piece = Piece(held_piece_prefab)
        held_piece_prefab = temp
    
    time_since_update = 0
    have_held = True

def place_falling_piece():
    global falling_piece
    global have_held
    global lines
    global input_move_interval
    global input_turn_interval
    global update_interval
    global alive

    y_levels = []
    for tile in falling_piece.tiles:
        ground_tiles[tile] = falling_piece.color
        
        if tile[1] not in y_levels:
            y_levels.append(tile[1])
    
    lines += check_for_full_lines(y_levels)
    
    falling_piece = Piece()
    for tile in falling_piece.tiles:
        if tile in ground_tiles:
            alive = False
            break
    
    have_held = False
    input_move_interval = BASE_INPUT_MOVE_INTERVAL
    input_turn_interval = BASE_INPUT_TURN_INTERVAL
    update_interval = BASE_UPDATE_INTERVAL

def update_falling_piece():
    next_positions = try_move_piece(falling_piece, 0, 1)
    if next_positions == None:
        place_falling_piece()
    else:
        falling_piece.tiles = next_positions
#endregion

def handle_key_input(input_keys):
    global input_move_interval
    global input_turn_interval
    global input_times

    inputs = [INPUTS_LEFT, INPUTS_RIGHT, INPUTS_UP, INPUTS_DOWN, INPUTS_CCW, INPUTS_CW, INPUTS_HOLD]
    input_intervals = 4 * [input_move_interval] + 2 * [input_turn_interval] + [0]
    functions = [lambda: try_move_piece(falling_piece, -1, 0), lambda: try_move_piece(falling_piece, 1, 0), lambda: slam_falling_piece(), lambda: try_move_piece(falling_piece, 0, 1), lambda: try_turn_falling_piece(False), lambda: try_turn_falling_piece(True), lambda: try_hold_falling_piece()]

    next_positions = None
    for i in range(len(inputs)):
        if any(input_keys[key] for key in inputs[i]) and pygame.time.get_ticks() >= input_times[i] + input_intervals[i]:
            next_positions = functions[i]()
            input_times[i] = pygame.time.get_ticks()
    
    if next_positions != None:
        falling_piece.tiles = next_positions

#region Draw graphics
def draw_tile_to_surface(position, color, surface: pygame.Surface):
    tile_border = pygame.Surface((GRID_SIZE, GRID_SIZE))
    tile_border.fill("#000000")
    tile_center = pygame.Surface((GRID_SIZE - 2 * TILE_PADDING, GRID_SIZE - 2 * TILE_PADDING))
    tile_center.fill(color)

    tile_border.blit(tile_center, (TILE_PADDING, TILE_PADDING))
    surface.blit(tile_border, (position[0] * GRID_SIZE, position[1] * GRID_SIZE))

def draw_board():
    board_surface = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT))
    board_surface.fill(pygame_utilities.colors['secondary'])

    for tile in ground_tiles:
        draw_tile_to_surface(tile, ground_tiles[tile], board_surface)
    
    ghost_piece = Piece((falling_piece.tiles, falling_piece.color, falling_piece.type), has_offset = False)
    while True:
        next_positions = try_move_piece(ghost_piece, 0, 1)
        if next_positions != None:
            ghost_piece.tiles = next_positions
        else:
            break
    for tile in ghost_piece.tiles:
        draw_tile_to_surface(tile, '#777777', board_surface)
    
    for tile in falling_piece.tiles:
        draw_tile_to_surface(tile, falling_piece.color, board_surface)
    
    screen.blit(board_surface, (WINDOW_PADDING, WINDOW_PADDING))

def draw_side_bar():
    global held_piece_prefab

    side_bar_surface = pygame.Surface((SIDE_BAR_WIDTH, BOARD_HEIGHT))
    side_bar_surface.fill(pygame_utilities.colors['secondary'])

    def draw_piece_on_side_bar(prefab, y_offset = 0):
        max_x = max(pos[0] for pos in prefab[0])
        offset = (SIDE_BAR_WIDTH / GRID_SIZE - 1 - max_x) / 2
        prefab[0] = [(pos[0] + offset, pos[1] + offset + y_offset) for pos in prefab[0]]

        for tile in prefab[0]:
            draw_tile_to_surface(tile, prefab[1], side_bar_surface)

    draw_piece_on_side_bar(Piece.get_next_piece_prefab())
        
    if held_piece_prefab != None:
        draw_piece_on_side_bar(list(held_piece_prefab), 4)
    
    side_bar_surface.blit(font.render(f"Lines {lines}", 1, pygame_utilities.colors['primary']), (GRID_SIZE, 8 * GRID_SIZE))
    
    screen.blit(side_bar_surface, (BOARD_WIDTH + 2 * WINDOW_PADDING, WINDOW_PADDING))

def draw_frame():
    screen.fill(pygame_utilities.colors['accent'])

    draw_board()
    draw_side_bar()
#endregion

def main():
    #region Globals
    global ground_tiles
    global falling_piece
    global held_piece_prefab
    global have_held
    global lines

    global input_move_interval
    global input_turn_interval
    global input_times

    global update_interval
    global time_since_update
    global alive
    #endregion

    ground_tiles = {}
    random.shuffle(Piece.prefabs)
    Piece.next_prefab_index = 0
    falling_piece = Piece()
    held_piece_prefab = None
    have_held = False
    lines = 0

    input_move_interval = BASE_INPUT_MOVE_INTERVAL
    input_turn_interval = BASE_INPUT_TURN_INTERVAL
    input_times = 4 * [-input_move_interval] + 2 * [-input_turn_interval] + [0]

    update_interval = BASE_UPDATE_INTERVAL
    time_since_update = 0

    alive = True
    while alive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        handle_key_input(pygame.key.get_pressed())

        time_since_update += game_clock.get_time()
        if time_since_update >= update_interval:
            if pygame.time.get_ticks() - input_times[3] >= input_move_interval or update_interval < BASE_UPDATE_INTERVAL:
                update_falling_piece()
            time_since_update = 0

        draw_frame()

        pygame.display.update()
        game_clock.tick(MAX_FPS)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((BOARD_WIDTH + 3 * WINDOW_PADDING + SIDE_BAR_WIDTH, BOARD_HEIGHT + 2 * WINDOW_PADDING))
    pygame.display.set_caption("Tetris")
    game_clock = pygame.time.Clock()
    font = pygame.font.SysFont('Impact', 30)

    playing = True
    while playing:
        main()