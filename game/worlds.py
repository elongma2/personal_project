from .tank import Tank
from .bullets import Bullet
from .asteroids import Asteroid
class world():
    def __init__(self,screen_rect):
        self.tank: dict[int,Tank] = {}
        self.bullets: list[Bullet] = []
        self.asteroids: list[Asteroid] = []
        self.screen_rect= screen_rect
        self.phase= "Playing"
        self.winner_id: int | None = None  
