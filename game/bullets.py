import pygame
BULLET_SPEED = 700         
BULLET_RADIUS = 4
BULLET_LIFETIME_MS = 1400
FIRE_COOLDOWN_MS = 180
class Bullet:
    def __init__(self,pos,direction,owner_id = None,speed=BULLET_SPEED,life_ms = BULLET_LIFETIME_MS,safe_until_ms = 0):
        self.pos = pygame.math.Vector2(pos)
        #normalize changes the vector from let say (300,400) to (0.3,0.4). this is prevent any overspeed
        self.vel = pygame.math.Vector2(direction).normalize() * speed
        self.life_ms = life_ms
        self.radius = BULLET_RADIUS
        self.owner_id = owner_id
        self.safe_until_ms = safe_until_ms
    
    def update(self,dt,screen_rect):
        self.pos += self.vel * dt
        self.life_ms -= dt * 1000
        if self.life_ms <= 0:
            return False
        if not screen_rect.inflate(50,50).collidepoint(self.pos.x,self.pos.y):
            return False
        return True
    
    def draw(self,surface):
        #bullets are expected to be in whole pixels
        pygame.draw.circle(surface, "white", (int(self.pos.x), int(self.pos.y)), self.radius)
        
    
   
        