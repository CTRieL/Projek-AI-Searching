import pygame
import numpy as np
from testing import AreaCalculator

class UI:
    def __init__(self, width=500, height=500, rows=10, cols=10):
        pygame.init()
        self.width = width
        self.height = height
        
        self.rows = rows
        self.cols = cols
        self.cell_size = width // cols
        
        self.WHITE = (255, 255, 255)
        self.GRAY = (200, 200, 200)
        self.BLUE = (50, 100, 255)
        self.RED = (255, 50, 50)
        self.BLACK = (0, 0, 0)
        self.FONT = pygame.font.SysFont("Arial", 28)
        
        self.grid = np.zeros((rows, cols), dtype=int)
        self.highlight = np.zeros_like(self.grid, dtype=bool)

        self.screen = pygame.display.set_mode((width, height))
        
        pygame.display.set_caption("Tata Letak Furnitur")
        self.calc = AreaCalculator()
        
        self.state = 'input'  # 'input' atau 'main'
        
        self.input_name = ''
        self.input_length = ''
        self.input_width = ''
        self.furnitures = []
        self.input_field = 'name'  # 'name', 'length', 'width'

    def draw_input_screen(self):
        self.screen.fill(self.WHITE)
        title = self.FONT.render('Input Furnitur', True, self.BLACK)
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 30))
        y = 100
        
        # Nama
        name_label = self.FONT.render('Nama:', True, self.BLACK)
        self.screen.blit(name_label, (50, y))
        name_val = self.FONT.render(self.input_name + ('|' if self.input_field=='name' else ''), True, self.BLUE)
        self.screen.blit(name_val, (180, y))
        
        # Panjang
        y += 40
        len_label = self.FONT.render('Panjang:', True, self.BLACK)
        self.screen.blit(len_label, (50, y))
        len_val = self.FONT.render(self.input_length + ('|' if self.input_field=='length' else ''), True, self.BLUE)
        self.screen.blit(len_val, (180, y))
        
        # Lebar
        y += 40
        wid_label = self.FONT.render('Lebar:', True, self.BLACK)
        self.screen.blit(wid_label, (50, y))
        wid_val = self.FONT.render(self.input_width + ('|' if self.input_field=='width' else ''), True, self.BLUE)
        self.screen.blit(wid_val, (180, y))
        
        # Tombol tambah
        add_btn = self.FONT.render('[Enter] Tambah Furnitur', True, self.RED if self.input_field=='add' else self.BLACK)
        self.screen.blit(add_btn, (50, y+50))
        
        # List furnitur
        y += 100
        furn_label = self.FONT.render('Daftar Furnitur:', True, self.BLACK)
        self.screen.blit(furn_label, (50, y))
        for i, furn in enumerate(self.furnitures):
            furn_str = f"{furn['name']} ({furn['length']}x{furn['width']})"
            furn_item = self.FONT.render(furn_str, True, self.BLUE)
            self.screen.blit(furn_item, (70, y+30+i*30))
        
        # Petunjuk
        instr = self.FONT.render('Tab: Pindah Field, Enter: Tambah, F: Selesai Input', True, self.BLACK)
        self.screen.blit(instr, (20, self.height-40))

    def draw_main_screen(self):
        self.screen.fill(self.WHITE)
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                if self.grid[y][x]:
                    pygame.draw.rect(self.screen, self.BLUE, rect)
                elif self.highlight[y][x] == 1:
                    pygame.draw.rect(self.screen, self.RED, rect)
                pygame.draw.rect(self.screen, self.GRAY, rect, 1)
        # Legend
        legend = self.FONT.render('Tekan R: Reset, Spasi: Hitung Area, Esc: Kembali ke Input', True, self.BLACK)
        self.screen.blit(legend, (10, self.height-30))

    def run(self):
        running = True
        while running:
            if self.state == 'input':
                self.draw_input_screen()
            else:
                self.draw_main_screen()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif self.state == 'input':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_TAB:
                            if self.input_field == 'name':
                                self.input_field = 'length'
                            elif self.input_field == 'length':
                                self.input_field = 'width'
                            elif self.input_field == 'width':
                                self.input_field = 'add'
                            else:
                                self.input_field = 'name'
                        elif event.key == pygame.K_RETURN:
                            if self.input_field == 'add' or self.input_field == 'width':
                                if self.input_name and self.input_length.isdigit() and self.input_width.isdigit():
                                    self.furnitures.append({
                                        'name': self.input_name,
                                        'length': int(self.input_length),
                                        'width': int(self.input_width)
                                    })
                                    self.input_name = ''
                                    self.input_length = ''
                                    self.input_width = ''
                                    self.input_field = 'name'
                        elif event.key == pygame.K_f:
                            # Selesai input, masuk ke main screen
                            self.state = 'main'
                        elif event.key == pygame.K_BACKSPACE:
                            if self.input_field == 'name':
                                self.input_name = self.input_name[:-1]
                            elif self.input_field == 'length':
                                self.input_length = self.input_length[:-1]
                            elif self.input_field == 'width':
                                self.input_width = self.input_width[:-1]
                        else:
                            if self.input_field == 'name':
                                if event.unicode.isprintable():
                                    self.input_name += event.unicode
                            elif self.input_field == 'length':
                                if event.unicode.isdigit():
                                    self.input_length += event.unicode
                            elif self.input_field == 'width':
                                if event.unicode.isdigit():
                                    self.input_width += event.unicode
                
                elif self.state == 'main':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = 'input'
                        if event.key == pygame.K_SPACE:
                            self.highlight[:, :] = False
                            empty_matrix = (self.grid == 0).astype(int)
                            self.calc.maxArea(empty_matrix)
                            self.calc.highlightMaxArea(self.highlight)
                        if event.key == pygame.K_r:
                            self.grid = np.zeros((self.rows, self.cols), dtype=int)
                            self.highlight = np.zeros_like(self.grid, dtype=bool)
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mx, my = pygame.mouse.get_pos()
                        gx, gy = mx // self.cell_size, my // self.cell_size
                        if 0 <= gx < self.cols and 0 <= gy < self.rows:
                            self.grid[gy][gx] = 1 if self.grid[gy][gx] == 0 else 0
            pygame.display.flip()
        pygame.quit()
