import pygame
import random
from itertools import count

AST_TIERS = {
    "L": {"r": 58,"speed":120,"kids": 2 ,"child":"M"},
    "M": {"r": 36,"speed":170,"kids": 1,"child":"S"},
    "S": {"r": 20,"speed":240,"kids": 0,"child":None}
}   
asteroid_id_update = count(1)

class Asteroid():
    def __init__(self,pos,vel,tier):
        self.pos = pygame.math.Vector2(pos) #return a x and y pos
        self.vel = pygame.math.Vector2(vel)
        self.tier = tier
        self.radius = AST_TIERS[tier]["r"]
        self.id = None

    def update(self,dt,bounds):
        self.pos += self.vel * dt
        # X walls
        if self.pos.x - self.radius < bounds.left:
            self.pos.x = bounds.left + self.radius
            self.vel.x *= -1
        elif self.pos.x + self.radius > bounds.right:
            self.pos.x = bounds.right - self.radius
            self.vel.x *= -1

        # Y walls
        if self.pos.y - self.radius < bounds.top:
            self.pos.y = bounds.top + self.radius
            self.vel.y *= -1
        elif self.pos.y + self.radius > bounds.bottom:
            self.pos.y = bounds.bottom - self.radius
            self.vel.y *= -1

    def split(self):
        cfg = AST_TIERS[self.tier]
        if cfg["kids"] <= 0:
            return []
        
        child_tier = cfg["child"]
        children = []
        for _ in range(cfg["kids"]):
            dirv = pygame.math.Vector2(1,0).rotate(random.uniform(0,360))
            speed = AST_TIERS[child_tier]["speed"]
            spawn_pos = self.pos + dirv * 0.5 # give the spawn pos a little offset
            ast = Asteroid(spawn_pos, dirv * speed , child_tier)
            ast.id = next(asteroid_id_update)
            children.append(ast)
        return children
    
    def bullet_collide(self,bullet):
        return self.pos.distance_to(bullet.pos) <= self.radius + bullet.radius
    
    def draw(self,surface):
        pygame.draw.circle(surface,"white",(int(self.pos.x),int(self.pos.y)),self.radius)

    @classmethod
    def asteroid_snapshot(cls, ast:dict):
        obj = cls.__new__(cls)
        obj.pos = pygame.math.Vector2(ast["x"],ast["y"])
        obj.vel = pygame.math.Vector2(ast["vx"],ast["vy"])
        obj.radius = ast["radius"]
        return obj

def spawn_asteroid(bounds,tank_pos,min_dist,tier):
    rad = AST_TIERS[tier]["r"]
    #find until it reaches the satisfied pos 
    while  True:
        pos = pygame.math.Vector2(
            random.randint(bounds.left + rad , bounds.right - rad),
            random.randint(bounds.top + rad ,bounds.bottom - rad),
        )
        if pos.distance_to(tank_pos) >= min_dist:
            break
    vel = pygame.math.Vector2(1,0).rotate(random.randint(0,360)) * AST_TIERS[tier]["speed"]
    return Asteroid(pos,vel,tier)

