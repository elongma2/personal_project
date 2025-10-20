import pygame
import random
from game.worlds import world
from game.tank import Tank
from game.asteroids import Asteroid
from game.bullets import Bullet

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


def respawn_point(game_world,max_tries = 50, margin = 40):
    respawn_rect = game_world.screen_rect
    #ensure spawn point not to near to edges
    respawn_rect = respawn_rect.inflate(-2*margin,-2*margin)


    for _ in range(max_tries):
        x = random.randint(respawn_rect.left,respawn_rect.right) #x axis
        y = random.randint(respawn_rect.top,respawn_rect.bottom) #y axis
        pos = pygame.math.Vector2(x,y)

        not_collide = True
        for a in game_world.asteroids:
            if (pos - a.pos).length_squared() < (a.radius + margin)**2:
                not_collide = False
                break
        if not_collide:
            return x , y
    return respawn_rect.centerx, respawn_rect.centery


def simulate(dt: float, inputs_by_id: dict, now_ms: int, game_world: world) -> None:
    if getattr(game_world,"phase","") == "GAMEOVER":
        return
    # A) Update my tank from inputs
    for tid,tank in game_world.tank.items():
        inp = inputs_by_id[tid]
        if not inp:
            continue
        tank.update(inp,game_world.screen_rect)    

        # Fire (spawn bullets)
        if inp["fire"] and inp["aim"] is not None:
            tank.fire(game_world.bullets,now_ms,inp["aim"])

    # B) Update asteroids + check player-asteroid collision
    for a in game_world.asteroids:
        a.update(dt,game_world.screen_rect)

    collided_tanks = set()
    for a in game_world.asteroids:
        for tid,tank in game_world.tank.items():
            if tank.collision_check(a):
                if now_ms < tank.invuln_until :
                    continue
                collided_tanks.add(tid)

    eliminated_by_ast = []
    for tid in collided_tanks:
        if tid in game_world.tank:
            t = game_world.tank[tid]
            t.apply_damage(100)
            if t.hp < 0:
                spawnx,spawny = respawn_point(game_world,margin=40)
                if not t.try_respawn(now_ms,(spawnx,spawny)):
                    eliminated_by_ast.append(tid)

    if eliminated_by_ast:
        alive_tanks = [tid for tid,t in game_world.tank.items() if t.hp > 0]
        if len(alive_tanks) <= 1:
            game_world.phase = 'GAMEOVER'
            game_world.winner_id = alive_tanks[0] if len(alive_tanks) == 1 else None
            return

    # C) Update bullets & collisions
    remaining_bullets = [] #reset for next frame
    asteroids_to_add = []
    asteroids_to_remove = []

    for bullet in game_world.bullets:
        A = bullet.pos #previous position
        B = bullet.pos + bullet.vel * dt #new position

        earliest_t = 1.0
        hit_point = None
        hit_kind = None
        hit_target = None

        # 1) Check asteroids
        for a in game_world.asteroids:
            hit,t,Q = seg_circle_hit(A,B,a.pos,a.radius + bullet.radius)
            if hit and t < earliest_t:
                earliest_t = t
                hit_point = Q
                hit_kind = "ASTEROID"
                hit_target = a
        
        # 2) Check tanks
        for tid,tank in game_world.tank.items():
            if tid == bullet.owner_id and now_ms < bullet.safe_until_ms:
                continue

            hit,t,Q = seg_circle_hit(A,B,pygame.math.Vector2(tank.rect.center),tank.hitbox + bullet.radius)
            if hit and t < earliest_t:
                earliest_t = t
                hit_point = Q
                hit_kind = "TANK"
                hit_target = tank

        if hit_point is not None:
            bullet.pos = hit_point 

            if hit_kind == "ASTEROID":
                #split and remove asteroid
                new_ast = hit_target.split()
                asteroids_to_remove.append(hit_target)
                asteroids_to_add.extend(new_ast)
                continue
            
            elif hit_kind == "TANK":
                if hit_target.can_take_bullet(bullet,now_ms):
                    hit_target.apply_damage(50)
                    if not hit_target.try_respawn(now_ms):
                        game_world.phase = "GAMEOVER"
                        game_world.winner_id = bullet.owner_id
                continue
        else:
            # no hit → free flight
            bullet.pos = B 

        # C3: advance bullet if still alive
        remaining_bullets.append(bullet)

    game_world.bullets = remaining_bullets
    game_world.asteroids = [a for a in game_world.asteroids if a not in asteroids_to_remove]
    game_world.asteroids.extend(asteroids_to_add)

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
            "invuln" : max(0,tank.invuln_until - now_ms),
        }
    bullets = []
    for bullet in game_world.bullets:
        bullets.append({
            "id": bullet.id,
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
            "id": asteroid.id,
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
        "asteroids":asteroids,
        "phase":getattr(game_world,"phase","PLAYING"),
        "winner_id":getattr(game_world,"winner_id",None),
    }

def reconcile(state:list[dict],local_map:dict,make_fn,update_fn,grace_ms : int, now_ms: int | None = None):
    seen = set()
    for data in state:
        id = int(data["id"])
        seen.add(id)
        obj = local_map.get(id)
        if obj is None:
            obj = make_fn(data)
            setattr(obj,"_pending_delete_until",0)
            local_map[id] = obj
        else:
            update_fn(obj,data)
            setattr(obj,"_pending_delete_until",0)
    if grace_ms < 0:
        for id in list(local_map.keys()):
            if id not in seen:
                del local_map[id]
        return 
    if now_ms is None:
        now_ms = pygame.time.get_ticks()

    for id, obj in list(local_map.items()):
        if id not in seen:
            pd = getattr(obj,"_pending_delete_until",0)
            if pd == 0:
                setattr(obj,"_pending_delete_until",now_ms + grace_ms)
            elif now_ms >= pd:
                del local_map[id]
    
    
def apply_state(game_world:world, state:dict,now:float):
    for tid,tdata in state["tanks"].items():
        tid = int(tid)
        if tid not in game_world.tank:
            game_world.tank[tid] = Tank(
                0,0,"assets/tank_body.png","assets/tank_turret.png",tank_id=tid,headless=False
            )
        t = game_world.tank[tid]
        t.x = tdata.get("x")
        t.y = tdata.get("y")
        t.body_angle = tdata.get("body_angle")
        t.turret_angle = tdata.get("turret_angle")
        t.hp = tdata.get("hp")
        t.life = tdata.get("lives")
        t.rect.center = (t.x,t.y)

        if tdata.get("invuln") > 0:
            t.invuln_until = now + tdata["invuln"]
        else:
            t.invuln_until = 0

    #bullets update/create
    def mk_b(data):
        bullet = Bullet((0,0),(1,0),owner_id=data["owner_id"],safe_until_ms=data["life_ms"])
        bullet.id = data["id"]
        return bullet
    def up_b(bullet,data):
        bullet.pos.x = data["x"]
        bullet.pos.y = data["y"]
        bullet.vel.x = data["vx"]
        bullet.vel.y = data["vy"]
        bullet.life_ms = data["life_ms"]
    reconcile(state["bullets"],game_world.bullets_by_id,mk_b,up_b,grace_ms=0, now_ms=state["now_ms"])
    game_world.bullets = list(game_world.bullets_by_id.values())

    #asteroid updates/create
    def mk_a(data):
        ast = Asteroid.asteroid_snapshot(data)
        ast.id = data["id"]
        return ast
    def up_a(ast,data):
        ast.pos.x = data["x"]
        ast.pos.y = data["y"]
        ast.vel.x = data["vx"]
        ast.vel.y = data["vy"]
        ast.radius = data["radius"]
    reconcile(state["asteroids"],game_world.asteroids_by_id,mk_a,up_a,grace_ms=30, now_ms=state["now_ms"])
    game_world.asteroids = list(game_world.asteroids_by_id.values())

    game_world.phase = state.get("phase","PLAYING")
    game_world.winner_id = state.get("winner_id",None)

def clamp1(x) -> float:
    if x < 0 : return 0
    if x > 1.0 : return 1.0
    return float(x)
def lerp(second :float ,latest:float , t : float) -> float:
    return second + (latest - second) * t

def angle_lerp(second:float,latest:float, t:float) ->float:
    second = second % 360.0
    latest = latest % 360.0
    d = (latest - second + 540.0) % 360.0 - 180.0  # shortest signed delta
    return (second + d * t) % 360.0

def snap_selector(render_time:float ,snapshots: list) -> tuple:
    if not snapshots:
        return None,None
    first_server = snapshots[0][1]["now_ms"]
    last_server = snapshots[-1][1]["now_ms"]
    if render_time <= first_server: #check time 
        return snapshots[0],snapshots[0]
    if render_time >= last_server: #check time :
        return snapshots[-1],snapshots[-1]
    #else snapshot in the middle, get the prev and curr
    prev = snapshots[0]
    for curr in snapshots:
        if curr[1]["now_ms"] >= render_time:
            return prev,curr
        prev = curr
    return None,None

#CCD collision, find the closest point on the segment
def seg_circle_hit(A: pygame.math.Vector2, B: pygame.math.Vector2, 
                   C: pygame.math.Vector2, 
                   R: float):
    d = B - A #pos 2 - pos 1
    f = C - A #center of circle - pos 1
    dd = d.dot(d)

    if dd < 1e-8:
        Q = A
        hit = (Q-C).length_squared() < R*R
        return hit, 0.0, Q

    t = f.dot(d) / dd       # projection scalar
    t = clamp1(t)
    Q = A + d * (t)

    hit = (Q-C).length_squared() < R*R
    return hit, t, Q