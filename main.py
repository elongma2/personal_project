import sys
import pygame
import subprocess
from client import render_client
import time

def launch_server_subporcess():
    return subprocess.Popen([sys.executable, 'server.py'], stdout= sys.stdout, stderr=sys.stderr)

def draw_text_on_centered_screen(screen, text,height):
    font = pygame.font.SysFont("Arial", 32)
    text_surface = font.render(text,True,(255,255,255))
    text_rect = text_surface.get_rect(center =(screen.get_width()//2,height))
    screen.blit(text_surface,text_rect)

def ask_ip(screen):
    ip = ""
    font = pygame.font.SysFont("Arial", 32)
    input_rect = pygame.Rect((screen.get_width()-110)//2,260,140,50)
    color_active = pygame.Color('lightskyblue3')
    color_passive = pygame.Color('chartreuse4')
    color = color_passive
    active = False
    pygame.key.start_text_input()
    while True:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.key.stop_text_input()
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                active = input_rect.collidepoint(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: #this is enter key
                    pygame.key.stop_text_input()
                    return ip or None
                if event.key == pygame.K_BACKSPACE:
                    ip = ip[:-1] #minus one

            if event.type == pygame.TEXTINPUT and active:
                ch = event.text
                for c in ch:
                    if c.isdigit() or c == ".":
                        ip += c

        screen.fill((0,0,0))
        draw_text_on_centered_screen(screen,"Enter IP",180)
        if active:
            color = color_active
        else:
            color = color_passive
        pygame.draw.rect(screen,color,input_rect,2)
        text_surface = font.render(ip,True,(255,255,255))
        screen.blit(text_surface,(input_rect.x+5,input_rect.y+5))
        input_rect.w = max(100,text_surface.get_width()+10)
        pygame.display.flip()

def menu(screen):
    while True:
        screen.fill((10,10,12))
        draw_text_on_centered_screen(screen,"LAN Tank Wars",180)
        draw_text_on_centered_screen(screen, "[H] Host game   |   [J] Join game   |   [Q] Quit",260)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("QUIT",None)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return ("QUIT",None)
                if event.key == pygame.K_h:
                    return ("HOST",None)
                if event.key == pygame.K_j:
                    ip = ask_ip(screen)
                    if ip: return ("JOIN",ip)

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
                render_client(screen,"192.168.50.226",12345)
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
        

    