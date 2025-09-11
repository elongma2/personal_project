import pygame
from lan_setup.net_client import clientSocket
from game.worlds import world
from helper import draw,apply_state,collect_local_inputs
from game.remote_controller import LocalKBM

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280,720))
    clock = pygame.time.Clock()
    screen_rect = screen.get_rect()
    game_world = world(screen_rect)
    client_id = None

    #network setup
    client = clientSocket("127.0.0.1",12345)
    client.connect()

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
                apply_state(game_world,msg)
        
        #read and send input
        if client_id is not None:
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
        if game_world.phase == "GAMEOVER":
            running = False
        draw(screen,game_world,now)
    client.close()
    pygame.quit()

if __name__ == "__main__":
    main()
        

   