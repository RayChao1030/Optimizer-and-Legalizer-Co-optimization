import numpy as np
import argparse
from dataclasses import dataclass
from sortedcontainers import SortedDict
import cv2
import time
import multiprocessing

import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

RESOLUTION = [1920, 1080]
BUFFER_SIZE = 500000

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

@dataclass
class Row:
    y: float
    cells: SortedDict[float, Cell]

    def checkOverlap(self, x, width):
        if x in self.cells:
            return True
        idx = self.cells.bisect_right(x)
        if idx > 0:
            prev_x, prev_width = self.cells.peekitem(idx - 1)
            if prev_x + prev_width > x:
                return True
        
        # Check if it overlaps with the block to the right
        if idx < len(self.cells):
            next_x, _ = self.cells.peekitem(idx)
            if next_x < x + width:
                return True
        return False
    
    def getOverlapCells(self, x, width):
        overlap_cells: set[str] = set()
        idx = self.cells.bisect_right(x)
        if idx > 0:
            _, prev_cell = self.cells.peekitem(idx - 1)
            if prev_cell.x + prev_cell.width > x:
                overlap_cells.add(prev_cell)
        
        # Check if it overlaps with the block to the right
        if idx < len(self.cells):
            _, next_cell = self.cells.peekitem(idx)
            if next_cell.x < x + width:
                overlap_cells.add(next_cell)
        return overlap_cells 

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
        glutInit()
        if display:
            glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # Double buffer and RGB color mode
            glutInitWindowSize(*RESOLUTION)  # Set window size
            glutCreateWindow("Visualizer")  # Create window
            glutDisplayFunc(self.display)  # Register the display function
        else:
            glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)  # Double buffer and RGB color mode
            glutInitWindowSize(1, 1)  # Set window size
            glutCreateWindow("Visualizer")  # Create window
            glutHideWindow()

            # steup view port 
            glViewport(0, 0, *RESOLUTION)
            glutDisplayFunc(lambda *args: None)  # Register the display function
        
        
        glutReshapeFunc(self.reshape)  # Register the reshape function to handle window resizing

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


    # OpenGL reshape function
    def reshape(self, width, height):
        glViewport(0, 0, width, height)  # Set the viewport size
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.x0, self.x1, self.y0, self.y1, -1, 1)  # Adjust the scale as needed
        glMatrixMode(GL_MODELVIEW)

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
        glutSwapBuffers()  # Swap buffers for double buffering

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
    rows: list[Row]
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 1
    visualizer: Canva

    def __init__(self, display = False):
        self.cells = {}
        self.rows = []
        self.cells_mapping = SortedDict()
        self.display = display

    def parser(self, lg_filename: str):
        with open(lg_filename, "r") as input:
            lg_lines = input.readlines()
        self.x0, self.y0, self.x1, self.y1 = map(float, lg_lines[2].strip().split(' ')[1:])
        self.visualizer = Canva(self.x0, self.y0, self.x1, self.y1, self.display)
        lg_lines = lg_lines[3:] 
        rows_y = []
        row_x = -1
        for i, line in enumerate(lg_lines):
            line = line.strip()
            if line.startswith("PlacementRows"):
                x, y, width, height, num = map(float, line.split(' ')[1:])
                self.lower_row_y = min(self.lower_row_y, y)
                self.row_height = height
                rows_y.append(y)
            else:
                name, x, y, width, height, fix = line.split(' ')
                self.cells[name] = Cell(name, float(x), float(y), float(width), float(height), True if fix == "FIX" else False, False, -1)
                
        for cell in self.cells.values():
            self.insertCell(cell)
            self.visualizer.pushCell(cell)
            self.cells_mapping[cell.pos] = cell.name
        self.visualizer.updateAllBuffer()

    def checkOverlap(self, cell: Cell):
        start_row = int((cell.y - self.lower_row_y)/self.row_height)

        row_idx = start_row
        while row_idx < len(self.rows) and self.rows[row_idx].y < cell.y + cell.height:
            overlap = self.rows[row_idx].checkOverlap(cell.x, cell.width)
            if overlap:
                return True
            row_idx += 1

        return False
    
    def insertCell(self, cell: Cell):
        start_row = int((cell.y - self.lower_row_y)/self.row_height)

        row_idx = start_row
        while row_idx < len(self.rows) and self.rows[row_idx].y < cell.y + cell.height:
            assert cell.x not in self.rows[row_idx].cells
            self.rows[row_idx].cells[cell.x] = cell

    def deleteCell(self, cell: Cell):
        start_row = int((cell.y - self.lower_row_y)/self.row_height)

        row_idx = start_row
        while row_idx < len(self.rows) and self.rows[row_idx].y < cell.y + cell.height:
            assert cell.x in self.rows[row_idx].cells
            del self.rows[row_idx].cells[cell.x]

    # step for opt
    def step(self, optimzieStep: OptimizeStep):
        for cell_name in optimzieStep.removed_cells:
            # get last cell
            last_cell_idx, last_cell_name = self.cells_mapping.peekitem(-1)
            current_cell = self.cells[cell_name]
            # remove current cell by swap back to current and remove back
            self.visualizer.swapCell(last_cell_idx, current_cell.pos)
            self.visualizer.popCell()
            self.cells_mapping[current_cell.pos] = last_cell_name
            self.cells[last_cell_name].pos = current_cell.pos

            del self.cells_mapping[last_cell_idx]
            del self.cells[cell_name]

        self.cells[optimzieStep.added_cell.name] = optimzieStep.added_cell
        self.visualizer.pushCell(optimzieStep.added_cell)
        idx = optimzieStep.added_cell.pos
        self.cells_mapping[idx] = optimzieStep.added_cell.name
        self.cells[optimzieStep.added_cell.name].pos = idx

        for cell_name, (cell_x, cell_y) in optimzieStep.moved_cells:
            cell = self.cells[cell_name]
            cell.x = cell_x
            cell.y = cell_y
            self.visualizer.setCellPosition(cell)

        self.visualizer.updateAllBuffer()

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
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self.board.visualizer.fbo)

        self.n_step = -1

        # draw first frame
        if self.display:
            self.board.visualizer.display()
        else:
            self.board.visualizer.draw()

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
            self.board.visualizer.display()
        else:   
            self.board.visualizer.draw()
        return False

    def terminate(self):
        self.queue.put(None)
        self.video_process.join()
        print(f"visualization finish, cost: {time.time() - self.start_time} secs")
        if self.display:
            glutLeaveMainLoop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-lg',     type=str, required=True, help="lg file")
    parser.add_argument('-opt',    type=str, required=True, help="opt file")
    parser.add_argument('-postlg', type=str, required=True, help="post file")
    parser.add_argument('-o',      type=str, help="output mp4 file")
    parser.add_argument('-display', action='store_true', help="render screen")
    parser.add_argument('-max_cell_num', type=int, default=500000, help="max # of cell can be handled")
    args = parser.parse_args()   
    lg_file = args.lg 
    opt_file = args.opt
    post_file = args.postlg
    output_file = args.o
    BUFFER_SIZE = args.max_cell_num

    #display = output_file is None
    display = True if args.display else False
    visualizer = Visualizer(lg_file, opt_file, post_file, output_file, display)

    if display:
        glutIdleFunc(visualizer.step)
        glutMainLoop()
    else:
        while not visualizer.step():
            pass
