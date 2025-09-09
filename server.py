import pygame
import random

from game.worlds import world
from game.tank import Tank
from game.asteroids import spawn_asteroid,Asteroid
from lan_setup.net_server import serverSocket
from helper import simulate,build_snapshot

def create_spawn_area():
    pass
def main():
    pygame.init()
    clock = pygame.time.Clock()
    screen_rect = pygame.Rect(0,0,1280,720)
    game_world = world(screen_rect)

    #spawn asteroids
    game_world.asteroids = [spawn_asteroid(screen_rect,pygame.math.Vector2(screen_rect.center),100,random.choice(["L","M","S"])) for _ in range(5)]

    #network
    server = serverSocket("127.0.0.1",12345)
    server.listen()

    #sim state
    inputs_by_id = {}
    next_player_id = 1
    tick = 0
    accumulated_dt = 0.0
    snap_accum = 0.0
    FIXED_DT = 1/60
    running = True
    print("Running headless server")

    while running:
        frame_dt = clock.tick(60)/1000.0 #frame rate
        now = pygame.time.get_ticks()

        #1 accept new clients
        for (conn,address) in server.accept_new():
            pid = next_player_id
            next_player_id += 1
            game_world.tank[pid] = Tank(640,340,"assets/tank_body.png","assets/tank_turret.png",tank_id = pid, headless= True)
            inputs_by_id[pid] = {"fwd":0,"bwd":0,"left":0,"right":0,"fire":0,"aim":None}
            server.send_line(conn, {"type":"welcome","id":pid})

        #2 get info from client
        for client in list(server.clients):
            try:
                for msg in server.poll_lines(client):
                    if not isinstance(msg,dict): continue
                    if msg["type"] == "input":
                        pid = int(msg["id"]) #client would have save the id
                        if pid in inputs_by_id:
                            inputs_by_id[pid] = {
                                "fwd":int(msg["fwd"]),
                                "bwd":int(msg["bwd"]),
                                "left":int(msg["left"]),
                                "right":int(msg["right"]),
                                "fire":int(msg["fire"]),
                                "aim":msg.get("aim",None)
                            }
            except Exception as e:
                server.drop(client)
                print(f"Dropping client: {e}")

        #3 simulate
        accumulated_dt += frame_dt
        if accumulated_dt > 0.25:
            accumulated_dt = 0.25
        
        while accumulated_dt >= FIXED_DT:
            simulate(FIXED_DT,inputs_by_id, now, game_world)
            tick += 1
            accumulated_dt -= FIXED_DT
        
        #4 send snapshot to clients
        snap_accum += frame_dt
        if snap_accum >= 0.08:
            snap_accum -= 0.08
            snap = build_snapshot(game_world,now,tick)
            #send snap to all clients
            server.broadcast(snap)
    server.close()
    print("Server shut down")

if __name__ == "__main__":
    main()
        
