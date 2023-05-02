import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

import game
import network
import client
import pygame_utilities

INPUTS_LEFT = [pygame.K_LEFT, pygame.K_a]
INPUTS_RIGHT = [pygame.K_RIGHT, pygame.K_d]
INPUTS_UP = [pygame.K_UP, pygame.K_w]
INPUTS_DOWN = [pygame.K_DOWN, pygame.K_s]
INPUTS_CCW = [pygame.K_z, pygame.K_COMMA]
INPUTS_CW = [pygame.K_x, pygame.K_PERIOD]
INPUTS_HOLD = [pygame.K_c, pygame.K_SLASH]

def handle_key_input(input_keys):
    inputs = [INPUTS_LEFT, INPUTS_RIGHT, INPUTS_UP, INPUTS_DOWN, INPUTS_CCW, INPUTS_CW, INPUTS_HOLD]
    input_intervals = 4 * [game_instance.input_move_interval] + 2 * [game_instance.input_turn_interval] + [0]
    functions = [lambda: game_instance.board.try_move_piece(game_instance.board.falling_piece, -1, 0), 
                 lambda: game_instance.board.try_move_piece(game_instance.board.falling_piece, 1, 0), 
                 lambda: game_instance.slam_falling_piece(), 
                 lambda: game_instance.board.try_move_piece(game_instance.board.falling_piece, 0, 1), 
                 lambda: game_instance.board.try_turn_falling_piece(False), 
                 lambda: game_instance.board.try_turn_falling_piece(True), 
                 lambda: game_instance.try_hold_falling_piece()]

    next_positions = None
    for i in range(len(inputs)):
        if any(input_keys[key] for key in inputs[i]) and pygame.time.get_ticks() >= input_times[i] + input_intervals[i]:
            next_positions = functions[i]()
            input_times[i] = pygame.time.get_ticks()
    
    if next_positions != None:
        game_instance.board.falling_piece.tiles = next_positions

#region Draw graphics
def draw_tiles_to_surface(dict_or_piece: dict | game.Piece, surface: pygame.Surface):
    is_dict = isinstance(dict_or_piece, dict)
    tiles = dict_or_piece if is_dict else dict_or_piece.tiles

    for tile in tiles:
        tile_border = pygame.Surface((game.GRID_SIZE, game.GRID_SIZE))
        tile_border.fill("#000000")
        tile_center = pygame.Surface((game.GRID_SIZE - 2 * game.TILE_PADDING, game.GRID_SIZE - 2 * game.TILE_PADDING))
        tile_center.fill(tiles[tile] if is_dict else dict_or_piece.color)

        tile_border.blit(tile_center, (game.TILE_PADDING, game.TILE_PADDING))
        surface.blit(tile_border, (tile[0] * game.GRID_SIZE, tile[1] * game.GRID_SIZE))

def draw_board(board: game.Board, position: tuple[int]):
    background_color = pygame_utilities.colors['secondary']
    board_surface = pygame.Surface((game.BOARD_WIDTH, game.BOARD_HEIGHT))
    board_surface.fill(background_color)

    draw_tiles_to_surface(board.ground_tiles, board_surface)
    
    ghost_piece = game.Piece((board.falling_piece.tiles, background_color, board.falling_piece.type), has_offset = False)
    for i in range(game.BOARD_TILE_HEIGHT):
        next_positions = board.try_move_piece(ghost_piece, 0, 1)
        if next_positions != None:
            ghost_piece.tiles = next_positions
        else:
            break
    draw_tiles_to_surface(ghost_piece, board_surface)
    
    draw_tiles_to_surface(board.falling_piece, board_surface)
    
    screen.blit(board_surface, position)

def draw_side_bar():
    side_bar_surface = pygame.Surface((game.SIDE_BAR_WIDTH, game.BOARD_HEIGHT))
    side_bar_surface.fill(pygame_utilities.colors['secondary'])

    def draw_piece_on_side_bar(prefab, y_offset = 0):
        max_x = max(pos[0] for pos in prefab[0])
        offset = (game.SIDE_BAR_WIDTH / game.GRID_SIZE - 1 - max_x) / 2
        prefab[0] = [(pos[0] + offset, pos[1] + offset + y_offset) for pos in prefab[0]]

        draw_tiles_to_surface(game.Piece(prefab, False), side_bar_surface)

    draw_piece_on_side_bar(game.Piece.get_next_piece_prefab())
        
    if game_instance.held_piece_prefab != None:
        draw_piece_on_side_bar(list(game_instance.held_piece_prefab), 4)
    
    side_bar_surface.blit(font.render(f"Lines {line_clears}", 1, pygame_utilities.colors['primary']), (game.GRID_SIZE, 8 * game.GRID_SIZE))
    
    screen.blit(side_bar_surface, (game.BOARD_WIDTH + 2 * game.WINDOW_PADDING, game.WINDOW_PADDING))

def draw_frame(player_board: game.Board, opponent_board: game.Board):
    screen.fill(pygame_utilities.colors['accent'])

    draw_board(player_board, (game.WINDOW_PADDING, game.WINDOW_PADDING))
    draw_side_bar()

    if paused:
        # Placeholder
        screen.blit(font.render("Waiting for Opponent", 1, pygame_utilities.colors['primary']), (25, 15))
    else:
        draw_board(opponent_board, (game.BOARD_WIDTH + 3 * game.WINDOW_PADDING + game.SIDE_BAR_WIDTH, game.WINDOW_PADDING))
#endregion

def create_request_flags():
    global line_clears

    flags = []
    if game_instance.alive:
        if line_clears > 0:
            flags = [network.Flag(network.REQUEST_SEND_LINES, line_clears)]
            line_clears = 0
    else:
        flags = [network.Flag(network.REQUEST_GAME_OVER, network.END_LOSE)]
    
    return flags

def handle_response_flags(flags: network.Flag | list[network.Flag]):
    global paused
    
    if isinstance(flags, network.Flag):
        flags = [flags]

    paused = False
    for flag in flags:
        if flag.command == network.RESPONSE_WAIT:
            paused = True
        elif flag.command == network.RESPONSE_ADD_LINES:
            game_instance.add_lines(flag.details)
        elif flag.command == network.RESPONSE_GAME_WON:
            paused = True

def update_game():
    global line_clears

    handle_key_input(pygame.key.get_pressed())

    game_instance.time_since_update += game_clock.get_time()
    if game_instance.time_since_update >= game_instance.update_interval:
        if pygame.time.get_ticks() - input_times[3] >= game_instance.input_move_interval or game_instance.update_interval < game.BASE_UPDATE_INTERVAL:
            line_clears = game_instance.try_apply_gravity()
        
        game_instance.time_since_update = 0

def main():
    global game_instance
    global input_times
    global line_clears
    global paused

    game_instance = game.Game()
    input_times = 4 * [-game_instance.input_move_interval] + 2 * [-game_instance.input_turn_interval] + [0]
    line_clears = 0
    paused = True

    while game_instance.alive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        if not paused:
            update_game()
        
        game_state = local_client.send_request(network.Request(game_instance.board, create_request_flags()))
        if game_state != None:
            handle_response_flags(game_state.flag_lists[local_client.id])

        opponent_board = game.Board.empty() if game_state == None else game_state.boards[1 - local_client.id]
        draw_frame(game_instance.board, opponent_board)

        pygame.display.update()
        game_clock.tick(game.MAX_FPS)

if __name__ == '__main__':
    local_client = client.Client()

    pygame.init()
    screen = pygame.display.set_mode((2 * game.BOARD_WIDTH + 4 * game.WINDOW_PADDING + game.SIDE_BAR_WIDTH, game.BOARD_HEIGHT + 2 * game.WINDOW_PADDING))
    pygame.display.set_caption(f"Tetris (Player {local_client.id + 1})")
    game_clock = pygame.time.Clock()
    font = pygame.font.SysFont('Impact', 30)

    main()