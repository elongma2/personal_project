import pygame
import math
from .bullets import Bullet

class Tank(pygame.sprite.Sprite):
    def __init__(self,x,y,image_path_tank_base, image_path_tank_turret,tank_id,life =2,headless = False):
        # Call the parent class (Sprite) constructor
        super().__init__()
        self.has_image = not headless
        self.tank_id = tank_id

        # --- SIM STATE (exists everywhere) ---
        self.x = float(x)
        self.y = float(y)
        self.body_angle = 0.0
        self.turret_angle = 0.0
        self.rotating_speed = 2
        self.turret_rotating_speed = 2
        self.speed = 0.0

        self.last_shot = 0
        self.firing_rate = 500
        self.muzzle_offset = 0
        self.hp = 100
        self.invuln_until = 0
        self.life = life

        # --- RENDER (client only) ---
        if self.has_image:
            base = pygame.image.load(image_path_tank_base).convert_alpha()
            self.body_base = pygame.transform.scale(base, (100,100))
            self.original_image = self.body_base

            turret = pygame.image.load(image_path_tank_turret).convert_alpha()
            self.body_turret = pygame.transform.scale(turret, (50, 50))
            self.turret = self.body_turret

            self.rect = self.body_base.get_rect(center=(self.x, self.y))
            self.hitbox = (self.rect.width // 2) * 0.85
        else:
            self.rect = pygame.Rect(x, y, 50, 50)
            self.hitbox = (self.rect.width // 2) * 0.85

    def update(self,controls):
        #1 handle movement
        if controls["fwd"]:
            self.speed = 2
        elif controls["bwd"]:
            self.speed = -2
        else:
            self.speed = 0

        #2 handle rotation
        if controls["left"]:
            self.body_angle += self.rotating_speed
        elif controls["right"]:
            self.body_angle -= self.rotating_speed
        
        
        # 3. Use trig to move in the direction of angle
        radians = math.radians(self.body_angle)
        vx = -self.speed * math.sin(radians)
        vy = -self.speed * math.cos(radians)
        self.x += vx
        self.y += vy
        self.rect.center = (self.x,self.y)

        if controls["aim"] is not None:
            #4 turret rotation using mouse
            # turret rotation using mouse (correct, no lag/offset)
            cx, cy = self.rect.center   # center, not topleft
            mx, my = controls["aim"]

            # flip Y so up is +Y in math, as atan2 uses normal cartesian coordinates so Y moving up is pos,Y moving down is neg
            # to compensate for this just set dy to negative so it inverts
            #imagine inveredt graph paper
            dx = mx - cx
            dy = - (my - cy)  
            angle_m = math.degrees(math.atan2(dy, dx))  # 0°=right, +90°=up
            self.turret_angle = angle_m - 90            # if sprite faces UP by default


    def fire(self,bullet_group,now_ms,mouse_pos):
        if now_ms - self.last_shot < self.firing_rate:
            return  # too soon to fire again
        
        cx,cy = self.rect.center
        mouse_x,mouse_y = mouse_pos

        #here no need invert cause we not using cartesian, we using the pygame screen coordinates
        dir_v = pygame.math.Vector2(mouse_x - cx, mouse_y - cy)
        if dir_v == pygame.math.Vector2(0,0):
            return

        bullet_group.append(Bullet((cx,cy),dir_v,owner_id = self.tank_id, safe_until_ms= now_ms + 120))
        self.last_shot = now_ms

    def collision_check(self,a):
        # Collision needs to know if the distance between centers is ≤ the sum of radii.
        tx,ty = self.rect.center
        rsum = self.hitbox + a.radius
        dx = tx - a.pos.x
        dy = ty - a.pos.y
        return (dx * dx + dy * dy) <= rsum * rsum

    def draw(self,surface):
        rotated_body = pygame.transform.rotate(self.original_image,self.body_angle)
        new_rect = rotated_body.get_rect(center = self.rect.center)
        surface.blit(rotated_body,new_rect)

        rotated_turret = pygame.transform.rotate(self.turret,self.turret_angle)
        turret_rect = rotated_turret.get_rect(center=(self.rect.center))
        surface.blit(rotated_turret,turret_rect)

    def overlaps_bullet(self, bullet):
        tx, ty = self.rect.center
        rsum = self.hitbox + bullet.radius
        dx = tx - bullet.pos.x
        dy = ty - bullet.pos.y
        return (dx * dx + dy * dy) <= rsum * rsum
    
    def can_take_bullet(self, bullet, now_ms):
        """Game rules: invulnerability + shooter's safe window."""
        # Ignore your own bullet during its initial safe window
        if bullet.owner_id == self.tank_id and now_ms < bullet.safe_until_ms:
            return False
        # Invulnerability after respawn
        if now_ms < self.invuln_until:
            return False
        return True
    
    def apply_damage(self,dmg):
        self.hp -= dmg
    def try_respawn(self,now_ms,respawn_pos = (200,200)):
        if self.hp > 0:
            return True
        #reduce life
        self.life -= 1
        if self.life > 0:
            #reset
            self.hp = 100
            self.x,self.y = respawn_pos
            self.rect.center = (self.x,self.y)
            self.invuln_until = now_ms + 1200 #1.2s invulnerability
            return True
        return False
        

