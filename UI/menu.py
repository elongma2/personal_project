import pygame
from UI.button import Button

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
        screen.blit(pygame.image.load("assets/menu_background.jpg"),(0,0))
        MENU_TEXT = pygame.font.Font("assets/fonts/press_start_2p.ttf", 32).render("LAN Tank Wars",True,(255,255,255))
        MENU_RECT = MENU_TEXT.get_rect(center=(screen.get_width()//2,180))

        HOST_BUTTON = Button(image=None, pos=(screen.get_width()//2, 280), 
                             text_input="HOST", 
                             font=pygame.font.Font("assets/fonts/press_start_2p.ttf", 32), 
                             base_color=("#d7fcd4"), hovering_color=("white"))

        JOIN_BUTTON = Button(image=None, pos=(screen.get_width()//2, 360), 
                             text_input="JOIN", 
                             font=pygame.font.Font("assets/fonts/press_start_2p.ttf", 32), 
                             base_color=("#d7fcd4"), hovering_color=("white"))
        
        QUIT_BUTTON = Button(image=None, pos=(screen.get_width()//2, 440), 
                             text_input="QUIT", 
                             font=pygame.font.Font("assets/fonts/press_start_2p.ttf", 32), 
                             base_color=("#d7fcd4"), hovering_color=("white"))
        
        screen.blit(MENU_TEXT,MENU_RECT)

        for button in [HOST_BUTTON,JOIN_BUTTON,QUIT_BUTTON]:
            button.changeColor(pygame.mouse.get_pos())
            button.update(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("QUIT",None)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if HOST_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    return ("HOST",None)
                if JOIN_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    ip = ask_ip(screen)
                    if ip: return ("JOIN",ip)
                if QUIT_BUTTON.checkForInput(pygame.mouse.get_pos()):
                    return ("QUIT",None)