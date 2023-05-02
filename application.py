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

def update_screen_size(is_multiplayer: bool = False):
    global screen

    multi_extra_width = game.BOARD_WIDTH + game.WINDOW_PADDING if is_multiplayer else 0
    screen = pygame.display.set_mode((3 * game.WINDOW_PADDING + game.BOARD_WIDTH + game.SIDE_BAR_WIDTH + multi_extra_width, 2 * game.WINDOW_PADDING + game.BOARD_HEIGHT))

def check_for_quit():
    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

def stop_playing():
    global playing

    playing = False

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

#region Draw menu
def create_buttons(parent_position: tuple[int], parent_size: tuple[int], texts: list[str], functions: list):
    button_width = 200
    button_height = 60
    button_x = (screen.get_width() - button_width) / 2
    base_y = parent_position[1] + parent_size[1] + 2 * game.WINDOW_PADDING
    delta_y = button_height + game.WINDOW_PADDING

    return [pygame_utilities.Button(button_x, base_y + delta_y * i, button_width, button_height, screen, text_font, text_color, texts[i], functions[i]) for i in range(len(texts))]

def draw_main_menu(title: tuple[pygame.Surface, tuple[int]], buttons: list[pygame_utilities.Button]):
    global playing

    screen.fill(pygame_utilities.colors['accent'])

    screen.blit(title[0], title[1])

    for button in buttons:
        button.update()

    if game_outcome != "":
        outcome_render = text_font.render(game_outcome, 1, text_color)
        outcome_position = ((screen.get_width() - outcome_render.get_width()) / 2, title[1][1] + title[0].get_height() + (buttons[0].buttonSurface.get_height() + game.WINDOW_PADDING) * len(buttons) + 3 * game.WINDOW_PADDING)
        screen.blit(outcome_render, outcome_position)
    
    pygame.display.update()
#endregion

#region Draw game
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
    
    side_bar_surface.blit(text_font.render(f"Lines {line_clears}", 1, pygame_utilities.colors['primary']), (game.GRID_SIZE, 8 * game.GRID_SIZE))
    
    screen.blit(side_bar_surface, (game.BOARD_WIDTH + 2 * game.WINDOW_PADDING, game.WINDOW_PADDING))

def draw_game(player_board: game.Board, opponent_board: game.Board = None):
    screen.fill(pygame_utilities.colors['accent'])

    draw_board(player_board, (game.WINDOW_PADDING, game.WINDOW_PADDING))
    draw_side_bar()

    if paused:
        # Placeholder
        screen.blit(text_font.render("Waiting for Opponent", 1, pygame_utilities.colors['primary']), (25, 15))
    elif opponent_board != None:
        draw_board(opponent_board, (game.BOARD_WIDTH + 3 * game.WINDOW_PADDING + game.SIDE_BAR_WIDTH, game.WINDOW_PADDING))
    
    pygame.display.update()
#endregion

#region Multiplayer flags
def create_request_flags():
    global game_outcome
    global lines_to_send

    flags = []
    if game_instance.alive:
        if lines_to_send > 0:
            flags = [network.Flag(network.REQUEST_SEND_LINES, lines_to_send)]
            lines_to_send = 0
    else:
        flags = [network.Flag(network.REQUEST_GAME_OVER, network.END_LOSE)]
        game_outcome = network.END_LOSE
    
    return flags

def handle_response_flags(flags: network.Flag | list[network.Flag]):
    global game_outcome
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
            game_outcome = network.END_WIN
#endregion

def update_game():
    global lines_to_send
    global line_clears

    handle_key_input(pygame.key.get_pressed())

    game_instance.time_since_update += game_clock.get_time()
    if game_instance.time_since_update >= game_instance.update_interval:
        if pygame.time.get_ticks() - input_times[3] >= game_instance.input_move_interval or game_instance.update_interval < game.BASE_UPDATE_INTERVAL:
            lines_to_send = game_instance.try_apply_gravity()
            line_clears += lines_to_send
        
        game_instance.time_since_update = 0

def play_game(is_multiplayer = False):
    global game_instance
    global input_times
    global lines_to_send
    global paused
    global line_clears
    global game_outcome

    if is_multiplayer:
        local_client = client.Client()
        if local_client.id == None:
            game_outcome = "Server Offline"
            return

    update_screen_size(is_multiplayer)

    game_instance = game.Game()
    input_times = 4 * [-game_instance.input_move_interval] + 2 * [-game_instance.input_turn_interval] + [0]
    lines_to_send = 0
    paused = False

    line_clears = 0
    game_outcome = ""

    while game_instance.alive and game_outcome == "":
        check_for_quit()
        
        if not paused:
            update_game()
        
        if is_multiplayer:
            game_state = local_client.send_request(network.Request(game_instance.board, create_request_flags()))
            if game_state != None:
                handle_response_flags(game_state.flag_lists[local_client.id])

        opponent_board = (game.Board.empty() if game_state == None else game_state.boards[1 - local_client.id]) if is_multiplayer else None
        draw_game(game_instance.board, opponent_board)

        game_clock.tick(game.MAX_FPS)
    
    if game_outcome != "":
        game_outcome += ": "
    game_outcome += f" Cleared {line_clears} lines"
    
    if is_multiplayer:
        update_screen_size()

def main_menu():
    global playing
    global line_clears
    global game_outcome

    title_render = title_font.render("Tetris", 1, text_color)
    title_position = ((screen.get_width() - title_render.get_width()) / 2, 2 * game.WINDOW_PADDING)

    texts = ["Singleplayer", "Mutliplayer", "Quit"]
    functions = [lambda: play_game(), lambda: play_game(True), lambda: stop_playing()]
    buttons = create_buttons(title_position, (title_render.get_width(), title_render.get_height()), texts, functions)

    playing = True
    line_clears = 0
    game_outcome = ""
    while playing:
        check_for_quit()

        draw_main_menu((title_render, title_position), buttons)

        game_clock.tick(game.MAX_FPS)

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption("Tetris")
    update_screen_size()

    game_clock = pygame.time.Clock()
    title_font = pygame.font.SysFont('Impact', 90)
    text_font = pygame.font.SysFont('Impact', 30)
    text_color = '#FFFFFF'

    main_menu()