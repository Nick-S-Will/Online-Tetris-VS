import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

import game
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
    functions = [lambda: game_instance.try_move_piece(game_instance.falling_piece, -1, 0), lambda: game_instance.try_move_piece(game_instance.falling_piece, 1, 0), lambda: game_instance.slam_falling_piece(), lambda: game_instance.try_move_piece(game_instance.falling_piece, 0, 1), lambda: game_instance.try_turn_falling_piece(False), lambda: game_instance.try_turn_falling_piece(True), lambda: game_instance.try_hold_falling_piece()]

    next_positions = None
    for i in range(len(inputs)):
        if any(input_keys[key] for key in inputs[i]) and pygame.time.get_ticks() >= input_times[i] + input_intervals[i]:
            next_positions = functions[i]()
            input_times[i] = pygame.time.get_ticks()
    
    if next_positions != None:
        game_instance.falling_piece.tiles = next_positions

#region Draw graphics
def draw_tile_to_surface(position, color, surface: pygame.Surface):
    tile_border = pygame.Surface((game.GRID_SIZE, game.GRID_SIZE))
    tile_border.fill("#000000")
    tile_center = pygame.Surface((game.GRID_SIZE - 2 * game.TILE_PADDING, game.GRID_SIZE - 2 * game.TILE_PADDING))
    tile_center.fill(color)

    tile_border.blit(tile_center, (game.TILE_PADDING, game.TILE_PADDING))
    surface.blit(tile_border, (position[0] * game.GRID_SIZE, position[1] * game.GRID_SIZE))

def draw_board():
    board_surface = pygame.Surface((game.BOARD_WIDTH, game.BOARD_HEIGHT))
    board_surface.fill(pygame_utilities.colors['secondary'])

    for tile in game_instance.ground_tiles:
        draw_tile_to_surface(tile, game_instance.ground_tiles[tile], board_surface)
    
    ghost_piece = game.Piece((game_instance.falling_piece.tiles, game_instance.falling_piece.color, game_instance.falling_piece.type), has_offset = False)
    while True:
        next_positions = game_instance.try_move_piece(ghost_piece, 0, 1)
        if next_positions != None:
            ghost_piece.tiles = next_positions
        else:
            break
    for tile in ghost_piece.tiles:
        draw_tile_to_surface(tile, pygame_utilities.colors['secondary'], board_surface)
    
    for tile in game_instance.falling_piece.tiles:
        draw_tile_to_surface(tile, game_instance.falling_piece.color, board_surface)
    
    screen.blit(board_surface, (game.WINDOW_PADDING, game.WINDOW_PADDING))

def draw_side_bar():
    side_bar_surface = pygame.Surface((game.SIDE_BAR_WIDTH, game.BOARD_HEIGHT))
    side_bar_surface.fill(pygame_utilities.colors['secondary'])

    def draw_piece_on_side_bar(prefab, y_offset = 0):
        max_x = max(pos[0] for pos in prefab[0])
        offset = (game.SIDE_BAR_WIDTH / game.GRID_SIZE - 1 - max_x) / 2
        prefab[0] = [(pos[0] + offset, pos[1] + offset + y_offset) for pos in prefab[0]]

        for tile in prefab[0]:
            draw_tile_to_surface(tile, prefab[1], side_bar_surface)

    draw_piece_on_side_bar(game.Piece.get_next_piece_prefab())
        
    if game_instance.held_piece_prefab != None:
        draw_piece_on_side_bar(list(game_instance.held_piece_prefab), 4)
    
    side_bar_surface.blit(font.render(f"Lines {lines}", 1, pygame_utilities.colors['primary']), (game.GRID_SIZE, 8 * game.GRID_SIZE))
    
    screen.blit(side_bar_surface, (game.BOARD_WIDTH + 2 * game.WINDOW_PADDING, game.WINDOW_PADDING))

def draw_frame():
    screen.fill(pygame_utilities.colors['accent'])

    draw_board()
    draw_side_bar()
#endregion

def main():
    global game_instance
    global input_times
    global lines

    game_instance = game.Game()
    input_times = 4 * [-game_instance.input_move_interval] + 2 * [-game_instance.input_turn_interval] + [0]
    lines = 0

    alive = True
    while alive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        handle_key_input(pygame.key.get_pressed())

        game_instance.time_since_update += game_clock.get_time()
        if game_instance.time_since_update >= game_instance.update_interval:
            if pygame.time.get_ticks() - input_times[3] >= game_instance.input_move_interval or game_instance.update_interval < game.BASE_UPDATE_INTERVAL:
                clears = game_instance.apply_gravity()
                if clears == -1:
                    alive = False
                else:
                    lines += clears
            game_instance.time_since_update = 0

        draw_frame()

        pygame.display.update()
        game_clock.tick(game.MAX_FPS)

if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((game.BOARD_WIDTH + 3 * game.WINDOW_PADDING + game.SIDE_BAR_WIDTH, game.BOARD_HEIGHT + 2 * game.WINDOW_PADDING))
    pygame.display.set_caption("Tetris")
    game_clock = pygame.time.Clock()
    font = pygame.font.SysFont('Impact', 30)

    playing = True
    while playing:
        main()