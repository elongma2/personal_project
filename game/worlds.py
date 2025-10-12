from .tank import Tank
from .bullets import Bullet
from .asteroids import Asteroid
class world():
    def __init__(self,screen_rect):
        self.tank: dict[int,Tank] = {}
        self.bullets: list[Bullet] = []
        self.asteroids: list[Asteroid] = []
        self.asteroids_by_id = {}
        self.bullets_by_id = {}
        self.screen_rect= screen_rect
        self.phase= "PLAYING"
        self.winner_id: int | None = None  
