import sys
import pygame
import subprocess
from client import render_client
import time
import socket
import pygame
from UI.menu import menu
from UI.menu import draw_text_on_centered_screen
def launch_server_subporcess():
    return subprocess.Popen([sys.executable, 'server.py'], stdout= sys.stdout, stderr=sys.stderr)

def main():
    pygame.init()
    screen = pygame.display.set_mode((1280,720))
    pygame.display.set_caption("LAN Tank Wars")
    
    while True:
        type,ip = menu(screen)
        if type == "QUIT":
            break
        if type == "HOST":
            server = launch_server_subporcess()
            time.sleep(0.3)
            try:
                host = socket.gethostbyname(socket.gethostname())
                render_client(screen,host,12345)
            finally:
                server.terminate()
            
        if type == "JOIN":
            ok = render_client(screen,ip,12345)
            if not ok:
                screen.fill((0,0,0))
                draw_text_on_centered_screen(screen,"Connection Refused",180)
                pygame.display.flip()
                time.sleep(2)
                continue

    pygame.quit()
if __name__ == "__main__":
    main()
        

    