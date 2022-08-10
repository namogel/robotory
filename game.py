from typing import Literal, Optional

import attr
from pygame.rect import Rect


PlayerColor = Literal["light", "dark"]
DiskColor = Literal["black", "white"]
RobotColor = Literal["black", "white", "red"]

DISK_COLORS = ("black", "white")
game: Optional["Game"] = None


@attr.s(auto_attribs=True)
class Tile:
    id: int
    x: int
    y: int
    player: int
    neighbours: tuple[int, ...]
    rect: Optional[Rect] = None
    disk: Optional[DiskColor] = None
    is_hover: bool = False


@attr.s(auto_attribs=True)
class Player:
    id: int
    is_playing: bool

    @property
    def can_refill(self):
        return len(game.get_disks(self.id)) < 4

    def refill(self, disk):
        disk.player = self.id

        if not any(d for d in game.disks if not d.player and d.color == "white") or not any(
            d for d in game.disks if not d.player and d.color == "black"
        ):
            p1 = sum(1 for r in game.robots if game.get_tile(r.tile).player == 1)
            game.winner = 1 if p1 >= 2 else 2

        if not self.can_refill:
            game.end_turn()

        return self.can_refill


@attr.s(auto_attribs=True)
class Robot:
    color: RobotColor
    tile: int
    is_hover = False
    rect: Optional[Rect] = None

    @property
    def can_move(self):
        colors = {"white": ("white",), "black": ("black",), "red": ("white", "black")}[self.color]
        return any(game.get_tile(t).disk in colors for t in game.get_tile(self.tile).neighbours)

    def can_move_to(self, tile):
        return bool(tile.disk) if self.color == "red" else self.color == tile.disk


@attr.s(auto_attribs=True)
class Disk:
    color: DiskColor
    player: Optional[int] = None
    rect: Optional[Rect] = None
    is_hover: bool = False
    pos: Optional[list[int, int]] = None


@attr.s(auto_attribs=True)
class Game:
    players: tuple[Player, Player]
    tiles: tuple["Tile", ...]
    robots: tuple[Robot, ...]
    disks: list[Disk, ...]
    state: Optional[tuple[str, Player]] = None
    winner: Optional[Player] = None

    @property
    def playing(self):
        return self.players[0] if self.players[0].is_playing else self.players[1]

    def get_tile(self, tile_id):
        return next(t for t in self.tiles if t.id == tile_id)

    def get_disks(self, player_id, color=None):
        if color:
            return [d for d in self.disks if d.player == player_id and d.color == color]
        else:
            return sorted((d for d in self.disks if d.player == player_id), key=lambda d: d.color)

    def put_disk(self, disk, tile):
        tile.disk = disk.color
        self.disks.remove(disk)
        self.end_turn()

    def move_robot(self, robot, tile):
        robot.tile = tile.id
        tile.disk = None
        if not robot.can_move:
            self.end_turn()

    def end_turn(self):
        self.state = None

        if self.players[1].is_playing:
            self.players[0].is_playing = True
            self.players[1].is_playing = False
        else:
            self.players[0].is_playing = False
            self.players[1].is_playing = True


def init_game():
    global game

    game = Game(
        players=(Player(1, True), Player(2, False)),
        tiles=(
            Tile(id=0, x=0, y=2, player=1, neighbours=(1, 4, 5)),
            Tile(id=1, x=0, y=4, player=1, neighbours=(0, 2, 4, 5, 6)),
            Tile(id=2, x=0, y=6, player=1, neighbours=(1, 3, 5, 6, 7)),
            Tile(id=3, x=0, y=8, player=2, neighbours=(2, 7, 8)),
            Tile(id=4, x=1, y=1, player=1, neighbours=(0, 5, 9, 10)),
            Tile(id=5, x=1, y=3, player=1, neighbours=(0, 1, 4, 6, 10, 11)),
            Tile(id=6, x=1, y=5, player=1, neighbours=(1, 2, 5, 7, 11, 12)),
            Tile(id=7, x=1, y=7, player=2, neighbours=(2, 3, 6, 8, 12, 13)),
            Tile(id=8, x=1, y=9, player=2, neighbours=(3, 7, 13, 14)),
            Tile(id=9, x=2, y=0, player=1, neighbours=(4, 10, 15)),
            Tile(id=10, x=2, y=2, player=1, neighbours=(4, 5, 9, 11, 15, 16)),
            Tile(id=11, x=2, y=4, player=1, neighbours=(5, 6, 10, 12, 16, 17)),
            Tile(id=12, x=2, y=6, player=2, neighbours=(6, 7, 11, 13, 17, 18)),
            Tile(id=13, x=2, y=8, player=2, neighbours=(7, 8, 12, 14, 18, 19)),
            Tile(id=14, x=2, y=10, player=2, neighbours=(8, 13, 19)),
            Tile(id=15, x=3, y=1, player=1, neighbours=(9, 10, 16, 20)),
            Tile(id=16, x=3, y=3, player=1, neighbours=(10, 11, 15, 17, 20, 21)),
            Tile(id=17, x=3, y=5, player=2, neighbours=(11, 12, 16, 18, 21, 22)),
            Tile(id=18, x=3, y=7, player=2, neighbours=(12, 17, 19, 22, 23)),
            Tile(id=19, x=3, y=9, player=2, neighbours=(13, 14, 18, 23)),
            Tile(id=20, x=4, y=2, player=1, neighbours=(15, 16, 21)),
            Tile(id=21, x=4, y=4, player=2, neighbours=(16, 17, 20, 22)),
            Tile(id=22, x=4, y=6, player=2, neighbours=(17, 18, 21, 23)),
            Tile(id=23, x=4, y=8, player=2, neighbours=(18, 19, 22)),
        ),
        robots=(Robot("black", 12), Robot("white", 17), Robot("red", 6)),
        disks=(
            [Disk(disk_color, 1) for disk_color in DISK_COLORS for _ in range(2)]
            + [Disk(disk_color, 2) for disk_color in DISK_COLORS for _ in range(2)]
            + [Disk(disk_color) for _ in range(10) for disk_color in DISK_COLORS]
        ),
    )

    return game
