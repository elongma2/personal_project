import pygame
from lan_setup.net_client import clientSocket
from game.worlds import world
from helper import draw,apply_state,collect_local_inputs,snap_selector,clamp1,lerp,angle_lerp
from game.remote_controller import LocalKBM
from collections import deque

def draw_gameover_banner(screen,game_world,client_id):
    if getattr(game_world, "phase", "PLAYING") != "GAMEOVER":
        return
    win_id = getattr(game_world, "winner_id", None)
    if client_id is None:
        text = "Game Over"
        color = (200,200,200)
    elif win_id is None:
        text = "Draw!"
        color = (240, 240, 80)
    elif win_id == client_id:
        text = "You Win!"
        color = (0, 255, 0)
    else:
        text = f"You Lose — Player {win_id} Wins"
        color = (255, 60, 60)

    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    font = pygame.font.SysFont("Arial", 56, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    screen.blit(surf, rect)


def render_client(screen,ip, port):
    clock = pygame.time.Clock()
    screen_rect = screen.get_rect()
    game_world = world(screen_rect)
    client_id = None
    snapshot_collections = deque(maxlen = 16)
    INTER_DELAY_MS = 100
    server_time_est_ms = None
    saw_gameover = False
    exit_at = None

    #network setup
    client = clientSocket(ip,port)
    client.connect()
    
    if not client.is_connected():
        return False
        
    running = True
    controller = LocalKBM()
    while running:
        frame_dt = clock.tick(60) / 1000.0
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
        
        for msg in client.poll_lines():
            if msg["type"] == "welcome":
                client_id = msg["id"]

            elif msg["type"] == "state":
                snapshot_collections.append((pygame.time.get_ticks(),msg))
                # initialize or pull-forward our server-time estimate
                if server_time_est_ms is None:
                    server_time_est_ms = msg["now_ms"]
                else:
                    # ensure estimate never lags behind the newest server time
                    if msg["now_ms"] > server_time_est_ms:
                        server_time_est_ms = msg["now_ms"]
                apply_state(game_world,msg,now)
                if msg.get("phase") == "GAMEOVER":
                    saw_gameover = True
                    exit_at = now + 1500
 
        # advance our local estimate smoothly every frame
        if server_time_est_ms is not None:
            server_time_est_ms += frame_dt * 1000.0

        #read and send input
        if client_id is not None and client.is_connected() and not saw_gameover:
            input = collect_local_inputs(controller)
            client.send_line({"type":"input",
                              "id":client_id,
                              "fwd" : input["fwd"],
                              "bwd" : input["bwd"],
                              "left" : input["left"],
                              "right" : input["right"],
                              "fire" : input["fire"],
                              "aim" : input.get("aim",None)
                            })
            client.flush()
        
        #interpolationss
        if len(snapshot_collections) > 2:
            render_time = server_time_est_ms - INTER_DELAY_MS
            pair_prev, pair_curr = snap_selector(render_time,snapshot_collections)
            if pair_prev is not None:
                _,s_prev = pair_prev
                _,s_curr = pair_curr
                if "tick" in s_prev and "tick" in s_curr:
                    dt_ticks = max(1,s_curr["tick"] - s_prev["tick"])
                    dt_ms = dt_ticks * (1000.0 / 60.0)
                    #server time.
                    t0 = s_prev["now_ms"]
                    t1 = t0 + dt_ms
                else:
                    t0 = s_prev["now_ms"]
                    t1 = s_curr["now_ms"]
                    dt_ms = max(1.0,t1-t0)
                r = min(max(render_time,t0),t1)
                alpha = (r - t0) / dt_ms

                #tanks
                prev_tank = s_prev.get("tanks",{})
                curr_tank = s_curr.get("tanks",{})
                for tid,t in game_world.tank.items():
                    key = str(tid)
                    p0 = prev_tank.get(key)
                    p1 = curr_tank.get(key)
                    if p0 and p1:
                        t.x = lerp(p0["x"],p1["x"],alpha)
                        t.y = lerp(p0["y"],p1["y"],alpha)
                        t.body_angle = angle_lerp(p0["body_angle"],p1["body_angle"],alpha)
                        t.turret_angle = angle_lerp(p0["turret_angle"],p1["turret_angle"],alpha)
                        t.rect.center = (t.x,t.y) 
                #asteroids by id
                ast_prev = {}
                ast_curr = {}
        
                for a in s_prev.get('asteroids',[]):
                    key = int(a.get('id'))
                    ast_prev[key] = a
                
                for a in s_curr.get('asteroids',[]):
                    key = int(a.get('id'))
                    ast_curr[key] = a
                
                for aid,a in game_world.asteroids_by_id.items():
                    p0 = ast_prev.get(aid)
                    p1 = ast_curr.get(aid)
                    if p0 and p1:
                        a.pos.x = lerp(p0["x"], p1["x"], alpha)
                        a.pos.y = lerp(p0["y"], p1["y"], alpha)
                    elif (p0 is None) and (p1 is not None):
                        # Birth: back-extrapolate using the SAME dt_ms we computed above (server timeline)
                        back_ms = (1.0 - alpha) * dt_ms
                        back_s = back_ms / 1000.0
                        vx = p1.get("vx", 0.0)
                        vy = p1.get("vy", 0.0)
                        a.pos.x = p1["x"] - vx * back_s
                        a.pos.y = p1["y"] - vy * back_s
                    elif (p0 is not None) and (p1 is None):
                        #fatal: forward extrapolate, as when the ast is killed, there is an lagged frame in p0
                        fwd_s = alpha * dt_ms /1000
                        vx = p0.get("vx", 0.0)
                        vy = p0.get("vy", 0.0)
                        a.pos.x = p0["x"] + vx * fwd_s
                        a.pos.y = p0["y"] + vy * fwd_s
                                
        #draw
        draw(screen,game_world,now)
        draw_gameover_banner(screen,game_world,client_id)
        pygame.display.flip()

        #exit
        if saw_gameover and now >= exit_at:
            running = False
        if saw_gameover and client.closed:
            running = False

    client.close()
    return True



        

   
