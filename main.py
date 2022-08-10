import time
from datetime import datetime

from pygame.surface import Surface

from game import init_game
import sys
import pygame
from pygame import Rect


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
SLATE_GRAY = (119, 136, 153)
LIGHT_GRAY = (211, 211, 211)
DARK_GRAY = (105, 105, 105)
RED = (255, 30, 70)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_WIDTH = 40
TILE_HEIGHT = 40
ROBOT_RADIUS = 10
DISK_RADIUS = 10
BOARD_WIDTH = 5 * TILE_WIDTH
BOARD_HEIGHT = 6 * TILE_HEIGHT
PADDING_WIDTH = (SCREEN_WIDTH - BOARD_WIDTH) / 2
PADDING_HEIGHT = (SCREEN_HEIGHT - BOARD_HEIGHT) / 2
PADDING_BOARD = (PADDING_WIDTH, PADDING_HEIGHT)
PADDING_POOL_1 = (PADDING_WIDTH, PADDING_HEIGHT / 2)
PADDING_POOL_2 = (PADDING_WIDTH, SCREEN_HEIGHT - PADDING_HEIGHT / 2)

PUT_DISK = "put_disk"
REFILL = "refill"
MOVE_ROBOT = "move_robot"


def debug():
    print(game.state)
    for d in game.get_disks(1):
        print(d)


def blink():
    return int(datetime.now().strftime("%S")) % 2


def does_hover(rect, pos, radius):
    if not rect:
        return False

    dx = rect.centerx - pos[0]
    dy = rect.centery - pos[1]
    return dx**2 + dy**2 <= radius**2


def reset(state=False):
    if state:
        game.state = None
    for disk in game.disks:
        disk.pos = None
        disk.is_hover = False
    for tile in game.tiles:
        tile.is_hover = False
    for robot in game.robots:
        robot.is_hover = False


def mouse_motion(pos):
    reset()

    if game.state and game.state[0] == PUT_DISK:
        game.state[1].pos = pos

    if robot := next((r for r in game.robots if does_hover(r.rect, pos, ROBOT_RADIUS)), None):
        if (not game.state and robot.can_move) or (
            game.state and game.state[0] == MOVE_ROBOT and robot == game.state[1]
        ):
            robot.is_hover = True

    if not game.state or game.state[0] != PUT_DISK:
        if disk := next((d for d in game.disks if does_hover(d.rect, pos, DISK_RADIUS)), None):
            if (
                # pick one's disk
                (not game.state and disk.player == game.playing.id)
                # pick a neutral disk
                or (not disk.player and game.playing.can_refill)
            ):
                disk.is_hover = True

    if game.state:
        if tile := next((t for t in game.tiles if t.rect.collidepoint(pos)), None):
            if game.state[0] == PUT_DISK or (
                game.state[0] == MOVE_ROBOT
                and game.state[1].can_move_to(tile)
                and tile.id in game.get_tile(game.state[1].tile).neighbours
            ):
                tile.is_hover = True


def mouse_button(pos):
    if disk := next((d for d in game.disks if d.is_hover), None):
        disk.is_hover = False
        if disk.player:
            game.state = (PUT_DISK, disk)
            disk.pos = pos
        else:
            if game.playing.refill(disk):
                game.state = (REFILL, game.playing)

    elif tile := next((t for t in game.tiles if t.is_hover), None):
        if game.state and game.state[0] in (PUT_DISK, MOVE_ROBOT):
            tile.is_hover = False
            if game.state[0] == "put_disk":
                game.put_disk(game.state[1], tile)
            elif game.state[0] == MOVE_ROBOT:
                game.move_robot(game.state[1], tile)

    elif robot := next((r for r in game.robots if r.is_hover), None):
        if not game.state:
            robot.is_hover = False
            game.state = (MOVE_ROBOT, robot, robot.tile)
        elif game.state and game.state[0] == MOVE_ROBOT and game.state[1] == robot:
            if game.state[2] == robot.tile:
                reset(state=True)  # robot hasn't moved
            else:
                game.end_turn()


def handle_game_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            reset(state=True)

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            debug()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_button(event.pos)

        elif event.type == pygame.MOUSEMOTION:
            mouse_motion(event.pos)

        else:
            mouse_motion(pygame.mouse.get_pos())


def handle_end_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()


def draw_text(content, surface, padding):
    font = pygame.font.SysFont(None, 24)
    text = font.render(content, True, BLACK)
    surface.blit(text, padding)


def draw_tile(tile):
    tile.rect = rect = Rect(
        PADDING_WIDTH + tile.x * TILE_WIDTH,
        PADDING_HEIGHT + tile.y * TILE_HEIGHT / 2,
        TILE_WIDTH,
        TILE_HEIGHT,
    )
    # draw tile
    pygame.draw.rect(screen, {1: LIGHT_GRAY, 2: DARK_GRAY}[tile.player], rect)
    # draw border
    pygame.draw.rect(
        screen,
        GOLD
        if tile.is_hover and not tile.disk and not any(tile.id == r.tile for r in game.robots)
        else BLACK,
        rect,
        width=1,
    )
    # draw disk if any
    if tile.disk:
        pygame.draw.circle(
            screen,
            {"black": BLACK, "white": WHITE}[tile.disk],
            tile.rect.center,
            DISK_RADIUS,
            width=2,
        )
        if tile.is_hover:
            pygame.draw.circle(screen, GOLD, tile.rect.center, DISK_RADIUS + 3, width=3)

    # draw robot if any
    if robot := next((r for r in game.robots if r.tile == tile.id), None):
        robot.rect = pygame.draw.circle(
            screen,
            {"black": BLACK, "white": WHITE, "red": RED}[robot.color],
            rect.center,
            ROBOT_RADIUS,
        )
        if robot.is_hover:
            pygame.draw.circle(screen, GOLD, robot.rect.center, ROBOT_RADIUS + 3, width=3)


def draw_board():
    board = Surface((BOARD_WIDTH, BOARD_HEIGHT))
    board.fill(SLATE_GRAY)
    screen.blit(board, PADDING_BOARD)

    for tile in game.tiles:
        draw_tile(tile)

    if game.state and game.state[0] == MOVE_ROBOT:
        robot = game.state[1]
        tile = game.get_tile(robot.tile)
        for n in tile.neighbours:
            n = game.get_tile(n)
            if robot.can_move_to(n):
                pygame.draw.line(
                    screen,
                    {"black": BLACK, "white": WHITE, "red": RED}[robot.color],
                    tile.rect.center,
                    n.rect.center,
                    width=2,
                )


def draw_players():
    for player in game.players:
        padding = {1: PADDING_POOL_1, 2: PADDING_POOL_2}[player.id]
        # draw pool surface
        pool = Surface((4 * 30, 30))
        pool.fill({1: LIGHT_GRAY, 2: DARK_GRAY}[player.id])
        screen.blit(pool, padding)

        # draw pool disks
        for i, disk in enumerate(game.get_disks(player.id)):
            disk.rect = pygame.draw.circle(
                screen,
                {"black": BLACK, "white": WHITE}[disk.color],
                disk.pos or (padding[0] + i * 30 + 15, padding[1] + 15),
                DISK_RADIUS,
                width=2,
            )
            if disk.is_hover:
                pygame.draw.circle(screen, GOLD, disk.rect.center, DISK_RADIUS + 3, width=3)

        # write player ids and who's playing
        draw_text(f"Player {player.id}", screen, (padding[0] - 70, padding[1] + 8))
        if player.is_playing and blink():
            draw_text("->", screen, (padding[0] - 90, padding[1] + 8))


def draw_neutral_pool():
    padding = (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT / 2.5)

    pool = Surface((5 * 30, 4 * 30))
    pool.fill(GRAY)
    screen.blit(pool, padding)

    if game.state and game.state[0] == REFILL:
        pygame.draw.rect(
            screen,
            GOLD,
            Rect(padding[0], padding[1], pool.get_width() + 2, pool.get_height() + 2),
            width=2,
        )

    for color, y_padding in (("black", 0), ("white", 2 * 30)):
        for i, disk in enumerate(game.get_disks(None, color)):
            disk.rect = pygame.draw.circle(
                screen,
                {"black": BLACK, "white": WHITE}[disk.color],
                (padding[0] + i % 5 * 30 + 15, padding[1] + i // 5 * 30 + 15 + y_padding),
                DISK_RADIUS,
                width=2,
            )
            if disk.is_hover:
                pygame.draw.circle(screen, GOLD, disk.rect.center, DISK_RADIUS + 3, width=3)


def draw_game():
    screen.fill(SLATE_GRAY)

    draw_board()
    draw_players()
    draw_neutral_pool()

    pygame.display.flip()


def draw_winner():
    padding = (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.45)
    s = Surface((160, 50))
    s.fill(GRAY)
    r = screen.blit(s, padding)

    draw_text(f"Player {game.winner} wins!", screen, (r.x + 20, r.centery - 5))
    pygame.display.flip()


if __name__ == "__main__":
    game = init_game()
    pygame.init()
    pygame.display.set_caption("Robotory")

    size = width, height = 800, 600
    screen = pygame.display.set_mode(size)

    while not game.winner:
        handle_game_events()
        draw_game()
        time.sleep(0.05)

    draw_winner()
    while 1:
        handle_end_events()
        time.sleep(0.05)
