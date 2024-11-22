import numpy as np
import argparse
from dataclasses import dataclass
from sortedcontainers import SortedDict
import cv2
import time
import multiprocessing
import glfw

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

RESOLUTION = [1920, 1080]
BUFFER_SIZE = -1

@dataclass(init=False)
class Cell:
    name: str
    x: float
    y: float
    width: float
    height: float
    is_fix: bool
    is_merge: bool
    color: tuple[float, float, float]
    # index in visualization buffer
    pos: int

    def __init__(self, name, x, y, width, height, is_fix, is_merge, pos):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_fix = is_fix
        self.is_merge = is_merge
        self.color = (0.0, 0.0, 1.0) if is_merge  else ((0.0, 1.0, 0.0) if is_fix else (1.0, 0.0, 0.0))
        self.pos = pos

class Canva:
    def __init__(self, x0, y0, x1, y1, display = True):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

        RESOLUTION[0] = int(RESOLUTION[1] * (x1 - x0) / (y1 - y0))
        self.vertices = np.empty((BUFFER_SIZE*8*3,), dtype=np.float32)
        self.vertices_color = np.empty((BUFFER_SIZE*8*3,), dtype=np.float32)
        self.vertex_num = 0

        self.initOpenGL(display)

    def initOpenGL(self, display):
        # GLUT setup and main loop
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        if not display:
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)     

        self.window = glfw.create_window(*RESOLUTION, "Visualizer", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
        
        glfw.make_context_current(self.window)

        glViewport(0, 0, *RESOLUTION)

        # off screen rendering
        # https://stackoverflow.com/questions/12157646/how-to-render-offscreen-on-opengl
        if not display:
            self.fbo = glGenFramebuffers(1)
            self.rbo = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_RGB8, *RESOLUTION)
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.fbo)
            glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self.rbo)

        glClearColor(1.0, 1.0, 1.0, 1.0)  # Set background color to white
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Set up the orthogonal projection to fit the rectangles in the window
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.x0, self.x1, self.y0, self.y1, -1, 1)  # Adjust for your data bounds
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Create VBOs for vertices and colors
        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        self.vbo_colors = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glBufferData(GL_ARRAY_BUFFER, self.vertices_color.nbytes, self.vertices_color , GL_STATIC_DRAW)

    def pushCell(self, cell: Cell):
        i = self.vertex_num
        cell.pos = i
        self.vertex_num += 1
        self.setCellPosition(cell)

        color = cell.color
        offset = i*8*3
        self.vertices_color[offset:offset+24] = color*8
    
    def updateVertexBuffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices.nbytes, self.vertices)  # Update the VBO with new vertices

    def updateColorBuffer(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices_color.nbytes, self.vertices_color)  # Update the VBO with new colors

    def updateAllBuffer(self):
        self.updateVertexBuffer()
        self.updateColorBuffer()

    def popCell(self):
        #assert self.vertex_num > 0
        self.vertex_num -= 1

    def swapCell(self, i, j):
        #assert i >= 0 and i < self.vertex_num
        #assert j >= 0 and i < self.vertex_num
        if i == j:
            return
        i*=24
        j*=24
        self.vertices[i:i+24], self.vertices[j:j+24] = self.vertices[j:j+24].copy(), self.vertices[i:i+24].copy()
        self.vertices_color[i:i+24], self.vertices_color[j:j+24] = self.vertices_color[j:j+24].copy(), self.vertices_color[i:i+24].copy()

    def setCellPosition(self, cell: Cell):
        i = cell.pos
        #assert i >= 0 and i < self.vertex_num
        x = cell.x
        y = cell.y
        width = cell.width
        height = cell.height
        offset = i*8*3
        self.vertices[offset:offset + 24] = [
            x, y, 0.0,
            x + width, y, 0.0,
            x + width, y, 0.0,
            x + width, y + height, 0.0,
            x + width, y + height, 0.0,
            x, y + height, 0.0,
            x, y + height, 0.0,
            x, y, 0.0
        ]

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT)

        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glVertexPointer(3, GL_FLOAT, 0, None)  # Set vertex pointer

        glEnableClientState(GL_COLOR_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glColorPointer(3, GL_FLOAT, 0, None)  # Set color pointer

        # Draw all rectangles with a single draw call
        glDrawArrays(GL_LINES, 0, self.vertex_num * 8)  # Each rectangle has 8 vertices (lines)

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        glFlush()

    # OpenGL display setup
    def display(self):
        self.draw()
        glfw.swap_buffers(self.window)

@dataclass
class OptimizeStep:
    removed_cells: list[str]
    original_insert_x: float
    original_insert_y: float
    added_cell: Cell
    moved_cells: tuple[str, tuple[float, float]]     

@dataclass
class Board:
    lower_row_y = float('inf')
    row_height = -1.
    cells: dict[str, Cell]
    cells_mapping: SortedDict[int, str]
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 1
    canva: Canva

    def __init__(self, display = False):
        self.cells = {}
        self.cells_mapping = SortedDict()
        self.display = display

    def parser(self, lg_filename: str):
        with open(lg_filename, "r") as input:
            lg_lines = input.readlines()
        self.x0, self.y0, self.x1, self.y1 = map(float, lg_lines[2].strip().split(' ')[1:])
        lg_lines = lg_lines[3:] 
        row_x = -1
        for i, line in enumerate(lg_lines):
            line = line.strip()
            if line.startswith("PlacementRows"):
                pass
            else:
                name, x, y, width, height, fix = line.split(' ')
                self.cells[name] = Cell(name, float(x), float(y), float(width), float(height), True if fix == "FIX" else False, False, -1)

        global BUFFER_SIZE
        BUFFER_SIZE = len(self.cells) + 10
        self.canva = Canva(self.x0, self.y0, self.x1, self.y1, self.display)
        for cell in self.cells.values():
            self.canva.pushCell(cell)
            self.cells_mapping[cell.pos] = cell.name
        self.canva.updateAllBuffer()

    # step for opt
    def step(self, optimzieStep: OptimizeStep):
        for cell_name in optimzieStep.removed_cells:
            # get last cell
            last_cell_idx, last_cell_name = self.cells_mapping.peekitem(-1)
            current_cell = self.cells[cell_name]
            # remove current cell by swap back to current and remove back
            self.canva.swapCell(last_cell_idx, current_cell.pos)
            self.canva.popCell()
            self.cells_mapping[current_cell.pos] = last_cell_name
            self.cells[last_cell_name].pos = current_cell.pos

            del self.cells_mapping[last_cell_idx]
            del self.cells[cell_name]

        self.cells[optimzieStep.added_cell.name] = optimzieStep.added_cell
        self.canva.pushCell(optimzieStep.added_cell)
        idx = optimzieStep.added_cell.pos
        self.cells_mapping[idx] = optimzieStep.added_cell.name
        self.cells[optimzieStep.added_cell.name].pos = idx

        for cell_name, (cell_x, cell_y) in optimzieStep.moved_cells:
            cell = self.cells[cell_name]
            cell.x = cell_x
            cell.y = cell_y
            self.canva.setCellPosition(cell)

        self.canva.updateAllBuffer()

def mp4Maker(queue: multiprocessing.Queue, output_file: str, width: int, height: int):
    video_out = cv2.VideoWriter(output_file, fourcc=cv2.VideoWriter_fourcc(*'mp4v'), 
                                fps=60, frameSize=(width, height)) 
    while True:
        pixels = queue.get()
        if pixels is None:
            break

        frame = np.frombuffer(pixels, dtype=np.uint8)
        frame = frame.reshape((height, width, 3))  # Reshape to the correct frame size
        frame = frame[::-1, :, :] # flip, since (0, 0) in opengl is on left top
        video_out.write(frame)

    video_out.release()

class Visualizer:
    def __init__(self, lg_file: str, opt_file: str, post_file: str, output_file: str, display: bool):
        self.start_time = time.time()
        self.board = Board(display)
        self.board.parser(lg_file)

        self.optimize_cases: list[OptimizeStep] = []
        self.optimizeStepInit(opt_file, post_file)

        self.video_out = False
        if output_file:
            self.video_out = True
            self.queue = multiprocessing.Queue()
            self.video_process = multiprocessing.Process(target=mp4Maker, args=(self.queue, output_file, *RESOLUTION))
            self.video_process.start()

        self.display = display

        if not self.display:
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self.board.canva.fbo)

        self.n_step = -1

        # draw first frame
        if self.display:
            self.board.canva.display()
        else:
            self.board.canva.draw()

    # combine post and opt data
    def optimizeStepInit(self, opt_file, post_file):
        with open(opt_file, "r") as file:
            opt_lines = file.readlines()
        with open(post_file, "r") as file:
            post_lines = file.readlines()

        for i in range(len(post_lines)):
            post_lines[i] = post_lines[i].strip()

        post_line_idx = 0
        for line in opt_lines:
            line = line.strip()
            parts = line.split(' ')

            name = parts[-5]
            original_x, original_y, width, height = map(float, parts[-4:])
            parts = parts[1:-6]

            removed_cells = []
            for part in parts:
                removed_cells.append(part)

            moved_cells = []
            x, y = map(float, post_lines[post_line_idx].split(' '))
            post_line_idx+=1
            moved_num = int(post_lines[post_line_idx]) 
            post_line_idx+=1
            for i in range(moved_num):
                parts = post_lines[post_line_idx].split(' ')
                moved_cells.append((parts[0], tuple(map(float, parts[1:]))))
                post_line_idx+=1

            self.optimize_cases.append(OptimizeStep(removed_cells, original_x, original_y, 
                                                    Cell(name, x, y, width, height, False, True, -1), moved_cells))
            
    # https://stackoverflow.com/questions/41126090/how-to-write-pyopengl-in-to-jpg-image
    def captureFrame(self):
        if not self.display:
            glReadBuffer(GL_COLOR_ATTACHMENT0)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        pixels = glReadPixels(0, 0, *RESOLUTION, GL_BGR, GL_UNSIGNED_BYTE)
        self.queue.put(pixels)
    
    # return finish or not
    def step(self):
        if self.video_out:
            self.captureFrame()

        # move to next step
        self.n_step += 1
        if self.n_step == len(self.optimize_cases):
            self.terminate()
            return True

        self.board.step(self.optimize_cases[self.n_step])

        if self.display:
            self.board.canva.display()
        else:   
            self.board.canva.draw()
        return False

    def terminate(self):
        self.queue.put(None)
        self.video_process.join()
        print(f"visualization finish, cost: {time.time() - self.start_time} secs")
        if self.display:
            #glutLeaveMainLoop()
            glfw.set_window_should_close(self.board.canva.window, True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-lg',     type=str, required=True, help="lg file")
    parser.add_argument('-opt',    type=str, required=True, help="opt file")
    parser.add_argument('-postlg', type=str, required=True, help="post file")
    parser.add_argument('-o',      type=str, help="output mp4 file")
    parser.add_argument('-display', action='store_true', help="render screen")
    args = parser.parse_args()   
    lg_file = args.lg 
    opt_file = args.opt
    post_file = args.postlg
    output_file = args.o

    #display = output_file is None
    display = True if args.display else False
    visualizer = Visualizer(lg_file, opt_file, post_file, output_file, display)

    if display:
        while not glfw.window_should_close(visualizer.board.canva.window):
            visualizer.step()         # Update state
            glfw.poll_events()  # Process events
    else:
        while not visualizer.step():
            pass
