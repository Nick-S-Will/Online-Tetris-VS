import pygame

colors = {'primary': '#FF7DD4', 'accent': '#D65AAD', 'secondary': '#4A263E'}

class Button():
    def __init__(self, x: int, y: int, width: int, height: int, screen: pygame.Surface, font: pygame.font.Font = None, text_color = '#000000', button_text = "", on_click_function = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen
        if font == None:
            font = pygame.font.SysFont('Arial', 20)
        self.buttonText = font.render(button_text, True, text_color)
        self.onclickFunction = on_click_function

        self.buttonSurface = pygame.Surface((self.width, self.height))
        self.buttonRect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.fillColors = {
            'normal': colors['primary'],
            'hover': colors['accent'],
            'pressed': colors['secondary'],
        }
        self.alreadyPressed = False
    
    def update(self):
        mousePos = pygame.mouse.get_pos()
        
        if self.buttonRect.collidepoint(mousePos):
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                if not self.alreadyPressed and self.onclickFunction != None:
                    self.onclickFunction()
                
                self.buttonSurface.fill(self.fillColors['pressed'])
                self.alreadyPressed = True
                
            else:
                self.buttonSurface.fill(self.fillColors['hover'])
                self.alreadyPressed = False
        else:
            self.buttonSurface.fill(self.fillColors['normal'])
        
        self.buttonSurface.blit(self.buttonText, [self.buttonRect.width/2 - self.buttonText.get_rect().width/2, self.buttonRect.height/2 - self.buttonText.get_rect().height/2])
        self.screen.blit(self.buttonSurface, self.buttonRect)