import pygame
class Controller():
    def __init__(self):
        self.control_dict = {
            "fwd":0,
            "bwd":0,
            "left":0,
            "right":0,
            "fire":0,
            "aim":None
        }

    def read(self):
        return self.control_dict

class LocalKBM(Controller):
    def __init__(self):
        super().__init__()
    def read(self):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        moused_press = pygame.mouse.get_pressed()

        self.control_dict["fwd"] = keys[pygame.K_w]
        self.control_dict["bwd"] = keys[pygame.K_s]
        self.control_dict["left"] = keys[pygame.K_a]
        self.control_dict["right"] = keys[pygame.K_d]
        self.control_dict["fire"] = moused_press[0]
        self.control_dict["aim"] = mouse_pos
        
        return self.control_dict