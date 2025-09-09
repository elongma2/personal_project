import pygame
from game.remote_controller import LocalKBM
from game.worlds import world
from game.tank import Tank
from game.asteroids import spawn_asteroid,Asteroid
from game.bullets import Bullet

""" pygame.init()
screen = pygame.display.set_mode((1280,720))
clock = pygame.time.Clock()
screen_rect = screen.get_rect()
game_world = world(screen_rect)
game_world.tank[1] = Tank(640,340,"assets/tank_body.png","assets/tank_turret.png",tank_id = 1)
game_world.tank[2] = Tank(300,300,"assets/tank_body.png","assets/tank_turret.png",tank_id = 2)
ZERO_INPUTS = {"fwd":0,"bwd":0,"left":0,"right":0,"fire":0,"aim":None}
controller_1 = LocalKBM()
game_world.asteroids = [spawn_asteroid(screen_rect,pygame.math.Vector2(game_world.tank[1].rect.center),100,random.choice(["L","M","S"])) for _ in range(5)] """

def collect_local_inputs(controller) -> dict:
    c = controller.read()
    return {
        "fwd": (c["fwd"]),
        "bwd": (c["bwd"]),
        "left": (c["left"]),
        "right": (c["right"]),
        "fire":(c["fire"]),
        "aim":c["aim"]
    }

def simulate(dt: float, inputs_by_id: dict, now_ms: int, game_world: world) -> None:
    # A) Update my tank from inputs
    for tid,tank in game_world.tank.items():
        inp = inputs_by_id[tid]
        tank.update(inp)

        # Fire (spawn bullets)
        if inp["fire"] and inp["aim"] is not None:
            tank.fire(game_world.bullets,now_ms,inp["aim"])

        # B) Update asteroids + check player-asteroid collision
        for a in game_world.asteroids:
            for tid,tank in game_world.tank.items():
                if tank.collision_check(a):
                    game_world.phase = "GAMEOVER"
                    game_world.winner_id = None
                    break
            a.update(dt,game_world.screen_rect)
        
    # C) Update bullets & collisions
    remaining_bullets = [] #reset for next frame
    new_asteroids = []

    for bullet in game_world.bullets:
        hit = False
        # C1: bullet vs asteroids
        for a in game_world.asteroids:
            if a.bullet_collide(bullet):
                game_world.asteroids.remove(a)
                new_asteroids.extend(a.split())
                hit = True
                break

        #2 hit tanks
        if not hit:
            for tid,t in game_world.tank.items():
                if tid == bullet.owner_id:
                    continue

                if t.overlaps_bullet(bullet):
                    if t.can_take_bullet(bullet,now_ms):
                        t.apply_damage(50)
                        hit = True
                        if t.hp <= 0 and not t.try_respawn(now_ms):
                            game_world.phase = "GAMEOVER"
                            game_world.winner_id = bullet.owner_id
                # pass-through on invuln: do nothing (keep bullet alive)

        # C3: advance bullet if still alive
        if not hit and bullet.update(dt,game_world.screen_rect):
            remaining_bullets.append(bullet)

    game_world.bullets = remaining_bullets
    game_world.asteroids.extend(new_asteroids)

def draw(screen, game_world: world, now_ms: int) -> None:
    screen.fill("black")
    
    for a in game_world.asteroids:
        a.draw(screen)
    for b in game_world.bullets:
        b.draw(screen)
    for t in game_world.tank.values():
        t.draw(screen)

        # optional: invul ring
        if now_ms < t.invuln_until:
            pygame.draw.circle(screen, (255,255,0), t.rect.center, int(t.hitbox), 2)
    pygame.display.flip()


# A snapshot of the game state to pass to client
def build_snapshot(game_world: world, now_ms: int,tick:int) -> dict:
    tanks = {} #new tank dict
    for tid,tank in game_world.tank.items():
        tanks[tid] = {
            "x" : tank.x,
            "y" : tank.y,
            "body_angle" : tank.body_angle,
            "turret_angle" : tank.turret_angle,
            "hp" : tank.hp,
            "lives" : tank.life,
            "invuln" : tank.invuln_until,
        }
    bullets = []
    for bullet in game_world.bullets:
        bullets.append({
            "x": bullet.pos.x,
            "y": bullet.pos.y,
            "vx": bullet.vel.x,
            "vy": bullet.vel.y,
            "owner_id": bullet.owner_id,
            "life_ms": bullet.life_ms
        })

    asteroids = []
    for asteroid in game_world.asteroids:
        asteroids.append({
            "x": asteroid.pos.x,
            "y": asteroid.pos.y,
            "vx": asteroid.vel.x,
            "vy": asteroid.vel.y,
            "radius": asteroid.radius
        })
    return {
        "type":"state",
        "tick":tick,
        "now_ms":now_ms,
        "tanks":tanks,
        "bullets":bullets,
        "asteroids":asteroids
    }

def apply_state(game_world:world, state:dict):
    for tid,tdata in state["tanks"].items():
        tid = int(tid)
        if tid not in game_world.tank:
            game_world.tank[tid] = Tank(
                0,0,"assets/tank_body.png","assets/tank_turret.png",tank_id=tid,headless=False
            )
        t = game_world.tank[tid]
        t.x = tdata["x"]
        t.y = tdata["y"]
        t.body_angle = tdata["body_angle"]
        t.turret_angle = tdata["turret_angle"]
        t.hp = tdata["hp"]
        t.life = tdata["lives"]
        t.invuln_until = tdata["invuln"]
        t.rect.center = (t.x,t.y)

    new_bullets = []
    for bdata in state["bullets"]:
        b = Bullet(
            (0,0),
            (1,0),
            owner_id=bdata["owner_id"],
            life_ms=bdata["life_ms"],
        )
        b.pos= pygame.math.Vector2(bdata["x"],bdata["y"])
        b.vel = pygame.math.Vector2(bdata["vx"],bdata["vy"])
        new_bullets.append(b)
    game_world.bullets = new_bullets

    new_asteroids = []
    for ast in state["asteroids"]:
        a = Asteroid.asteroid_snapshot(ast)
        new_asteroids.append(a)
    game_world.asteroids = new_asteroids
    
""" def main():
    FIXED_DT = 1/60
    accumulated_dt = 0.0
    running = True
    while running:
        frame_dt = clock.tick(60) / 1000.0
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        inputs = collect_local_inputs(controller_1) # my inputs only
        inputs_by_id = {
            1:inputs,
            2:ZERO_INPUTS
        }
        accumulated_dt += frame_dt

        # clamp accum to avoid spiral-of-death on lag spikes
        if accumulated_dt > 0.25: 
            accumulated_dt = 0.25

        while accumulated_dt >= FIXED_DT:
            simulate(FIXED_DT, inputs_by_id, now, game_world)
            draw(screen, game_world, now)
            accumulated_dt -= FIXED_DT

        if game_world.phase == "GAMEOVER":
            running = False
            print("Gameover")
            print("Winner: ", game_world.winner_id)
        draw(screen, game_world, now)
    pygame.quit()

if __name__ == "__main__":
    main() """