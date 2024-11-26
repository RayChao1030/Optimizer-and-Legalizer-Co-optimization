import argparse
from dataclasses import dataclass
import time
from sortedcontainers import SortedDict
import glfw
import ffmpeg
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *

RESOLUTION = [1920, 1080]

MERGE_COLOR = (0.0, 0.0, 1.0)
ACTIVE_MERGE_COLOR = (0.0, 1.0, 1.0)
NOTFIX_COLOR = (0.0, 1.0, 0.0)
FIX_COLOR = (1.0, 0.0, 0.0)
LEGAL_COLOR = (0.0, 1.0, 0.0)
ILLEGAL_COLOR = (1.0, 0.0, 0.0)

# override above setting in detail mode
DETAIL_NOTFIX_COLOR = (0.8, 0.8, 0.8)
DETAIL_FIX_COLOR = (0.4, 0.4, 0.4)
REMOVE_COLOR = (1.0, 1.0, 0.0)
ORIGINAL_MERGE_COLOR = (1.0, 0.0, 1.0)

class Cell:
    def __init__(self, name: str, x: float, y: float, width: float, height: float, 
                 is_fix: bool, is_merge: bool, pos: int):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_fix = is_fix
        self.is_merge = is_merge
        self.color = MERGE_COLOR if is_merge else (FIX_COLOR if is_fix else NOTFIX_COLOR)
        self.pos = pos # index in visualization buffer

class Canva:
    def __init__(self, x0: float, y0: float, x1: float, y1: float, buffer_size: int, display = True):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

        RESOLUTION[0] = int(RESOLUTION[1] * (x1 - x0) / (y1 - y0))
        self.vertices = np.empty((buffer_size*8*3,), dtype=np.float32)
        self.vertices_color = np.empty((buffer_size*8*3,), dtype=np.float32)
        self.vertex_num = 0
        self.merge_cell_init = False
        self.merge_cell_vertices = np.empty((4*3,), dtype=np.float32)
        self.merge_cell_vertices_color = np.array(ACTIVE_MERGE_COLOR*4, dtype=np.float32)

        self.initOpenGL(display)

    def initOpenGL(self, display: bool):
        # GLUT setup and main loop
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)
        glfw.window_hint(glfw.DEPTH_BITS, 24); 

        if not display:
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)     

        self.window = glfw.create_window(*RESOLUTION, "Visualizer", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
        
        glfw.make_context_current(self.window)

        glViewport(0, 0, *RESOLUTION)

        # also render if on depth clip range border
        # that is, render [zNear, zFar], not [zNear, zFar)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL) 
        
        # off screen rendering
        # https://stackoverflow.com/questions/12157646/how-to-render-offscreen-on-opengl
        if not display:
            self.fbo = glGenFramebuffers(1)
            self.rbo = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA, *RESOLUTION)
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self.fbo)
            backingWidth = glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_WIDTH)
            backingHeight = glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_HEIGHT)
            glFramebufferRenderbuffer(GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, self.rbo)
            # bind depth buffer
            # https://stackoverflow.com/questions/4378182/whats-wrong-with-using-depth-render-buffer-opengl-es-2-0
            self.depth_buffer = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, backingWidth, backingHeight)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.depth_buffer)

        glClearColor(1.0, 1.0, 1.0, 1.0)  # Set background color to white

        # Set up the orthogonal projection to fit the rectangles in the window
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # zNear, zFar is respect to camera at (0,0,0) looking at -z axis, 
        # zNear=1 means the nearest coordinate camera can see is 1 in front of camera, that is, -1
        # zFar=-1 means the farest coordinate camera can see is -1 in front of camera, that is, 1
        glOrtho(self.x0, self.x1, self.y0, self.y1, 1.0, -1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Create VBOs for vertices and colors
        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        self.vbo_colors = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glBufferData(GL_ARRAY_BUFFER, self.vertices_color.nbytes, self.vertices_color , GL_STATIC_DRAW)

        # Create VBOs for merge cell vertices and colors
        self.vbo_merge_cell_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_merge_cell_vertices)
        glBufferData(GL_ARRAY_BUFFER, self.merge_cell_vertices.nbytes, self.merge_cell_vertices, GL_STATIC_DRAW)
        self.vbo_merge_cell_colors = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_merge_cell_colors)
        glBufferData(GL_ARRAY_BUFFER, self.merge_cell_vertices_color.nbytes, self.merge_cell_vertices_color , GL_STATIC_DRAW)
        
        # merge cell color not change, update directly
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_merge_cell_colors)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.merge_cell_vertices_color.nbytes, self.merge_cell_vertices_color)

    def pushCell(self, cell: Cell):
        i = self.vertex_num
        cell.pos = i
        self.vertex_num += 1
        z = -1. if cell.is_merge else 1.0
        self.setCellPosition(cell, z)
        self.setCellColor(cell)
    
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

    def setCellPosition(self, cell: Cell, z = 1.):
        i = cell.pos
        #assert i >= 0 and i < self.vertex_num
        x = cell.x
        y = cell.y
        width = cell.width
        height = cell.height
        offset = i*8*3
        #  6----5
        # 7      4
        # |      |
        # 8      3
        #  1----2
        self.vertices[offset:offset + 24] = [
            x, y, z,
            x + width, y, z,
            x + width, y, z,
            x + width, y + height, z,
            x + width, y + height, z,
            x, y + height, z,
            x, y + height, z,
            x, y, z
        ]

    def setMergeCell(self, cell: Cell):
        x = cell.x
        y = cell.y
        w = cell.width
        h = cell.height
        self.merge_cell_init = True
        # 3 ---- 4
        # |      |
        # |      |
        # |      |
        # 1 ---- 2
        self.merge_cell_vertices[:] = [
            x, y, 0.0,
            x + w, y, 0.0,
            x, y + h, 0.0,
            x + w, y + h, 0.0,
        ]
        # Update the VBO with new vertices
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_merge_cell_vertices)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.merge_cell_vertices.nbytes, self.merge_cell_vertices)

    def setCellColor(self, cell: Cell):
        i = cell.pos
        color = cell.color
        offset = i*8*3
        self.vertices_color[offset:offset+24] = color*8

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glVertexPointer(3, GL_FLOAT, 0, None)  # Set vertex pointer

        glEnableClientState(GL_COLOR_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_colors)
        glColorPointer(3, GL_FLOAT, 0, None)  # Set color pointer

        # draw rectangle border lines
        glDrawArrays(GL_LINES, 0, self.vertex_num * 8)  # Each rectangle has 8 vertices (lines)

        if self.merge_cell_init:
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_merge_cell_vertices)
            glVertexPointer(3, GL_FLOAT, 0, None)  # Set vertex pointer

            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_merge_cell_colors)
            glColorPointer(3, GL_FLOAT, 0, None)  # Set color pointer

            # draw filled rectangle
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)  # Each rectangle has 4 vertices

        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)

        glFlush()

    # draw and swap buffer
    def display(self):
        self.draw()
        glfw.swap_buffers(self.window)

@dataclass
class OptimizeStep:
    removed_cells: list[str]
    merge_x: float
    merge_y: float
    added_cell: Cell
    moved_cells: list[tuple[str, tuple[float, float]]] 

class DetailStatus:
    REMOVE = 0
    MERGE = 1
    MOVE = 2
    SHOWRESULT = 3

class Board:
    def __init__(self, display = False):
        self.cells: dict[str, Cell] = {}
        self.cells_mapping = SortedDict()
        self.display = display

        self.illegal_cells: list[tuple[str, tuple[float, float]]] = []
        self.prev_moved_cells: list[Cell] = []

        self.contain_merge_cell = False
        self.prev_merge_cell_name: str = None
        self.detail_status = DetailStatus.SHOWRESULT

    def parser(self, lg_filename: str):
        with open(lg_filename, "r") as input:
            lg_lines = input.read().splitlines()
        self.x0, self.y0, self.x1, self.y1 = map(float, lg_lines[2].strip().split(' ')[1:])
        lg_lines = lg_lines[3:] 
        for line in lg_lines:
            if line.startswith("PlacementRows"):
                pass
            else:
                name, x, y, width, height, fix = line.split(' ')
                self.cells[name] = Cell(name, float(x), float(y), float(width), float(height), True if fix == "FIX" else False, False, -1)

        self.canva = Canva(self.x0, self.y0, self.x1, self.y1, len(self.cells) + 10, self.display)
        for cell in self.cells.values():
            self.canva.pushCell(cell)
            self.cells_mapping[cell.pos] = cell.name
        self.canva.updateAllBuffer()

    def isOverlap(self, cell1: Cell, cell2: Cell):
        return cell1.x < cell2.x + cell2.width and\
               cell1.x + cell1.width > cell2.x and\
               cell1.y < cell2.y + cell2.height and\
               cell1.y + cell1.height > cell2.y

    # step for opt
    def step(self, optimizeStep: OptimizeStep):
        # draw prev merge cell
        if self.prev_merge_cell_name is not None:
            cell = self.cells[self.prev_merge_cell_name]
            self.canva.pushCell(cell)
            idx = cell.pos
            self.cells_mapping[idx] = self.prev_merge_cell_name
            self.cells[self.prev_merge_cell_name].pos = idx

        # remove merged cell
        for cell_name in optimizeStep.removed_cells:
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

        self.cells[optimizeStep.added_cell.name] = optimizeStep.added_cell
        self.canva.setMergeCell(optimizeStep.added_cell)
        optimizeStep.added_cell.x = optimizeStep.merge_x
        optimizeStep.added_cell.y = optimizeStep.merge_y
        self.prev_merge_cell_name = optimizeStep.added_cell.name

        # move all cell
        for cell_name, (cell_x, cell_y) in optimizeStep.moved_cells:
            cell = self.cells[cell_name]
            cell.x = cell_x
            cell.y = cell_y
            self.canva.setCellPosition(cell)

        self.canva.updateAllBuffer()
        return True

    # step for opt in detail
    def detailStep(self, optimizeStep: OptimizeStep):
        match self.detail_status:
            case DetailStatus.REMOVE:
                # mark remove cell
                for cell_name in optimizeStep.removed_cells:
                    current_cell = self.cells[cell_name]
                    current_cell.color = REMOVE_COLOR
                    self.canva.setCellColor(current_cell)
                    self.canva.setCellPosition(current_cell, -1.)

                self.detail_status = DetailStatus.MERGE
            case DetailStatus.MERGE:
                # add merge cell
                name = optimizeStep.added_cell.name
                self.cells[name] = optimizeStep.added_cell
                self.prev_merge_cell_name = name
                optimizeStep.added_cell.color = ORIGINAL_MERGE_COLOR
                # draw merge cell on oringal position
                self.canva.pushCell(optimizeStep.added_cell)
                idx = optimizeStep.added_cell.pos
                self.cells_mapping[idx] = name
                self.cells[name].pos = idx

                self.illegal_cells.append((name, (optimizeStep.merge_x, optimizeStep.merge_y)))

                self.detail_status = DetailStatus.MOVE
            case DetailStatus.MOVE:
                moved_cell_name, move_to = self.illegal_cells.pop()
                moved_cell = self.cells[moved_cell_name]
                

                # move cell
                moved_cell.x = move_to[0]
                moved_cell.y = move_to[1]
                if moved_cell.name != optimizeStep.added_cell.name:
                    moved_cell.color = LEGAL_COLOR
                self.prev_moved_cells.append(moved_cell)
                if moved_cell.name == optimizeStep.added_cell.name: # merged cell
                    self.canva.setMergeCell(moved_cell)

                    # remove merged cell
                    for cell_name in optimizeStep.removed_cells:
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
                else:
                    self.canva.setCellColor(moved_cell)
                    self.canva.setCellPosition(moved_cell, -1.0)

                # mark all cell if overlap with current cell
                i = 0
                while i < len(optimizeStep.moved_cells):
                    cell_name, _ = optimizeStep.moved_cells[i]
                    cell = self.cells[cell_name]
                    if self.isOverlap(cell, moved_cell):
                        cell.color = ILLEGAL_COLOR
                        self.canva.setCellColor(cell)
                        self.canva.setCellPosition(cell, -0.7) # use to change z
                        # swap and pop back
                        optimizeStep.moved_cells[i], optimizeStep.moved_cells[-1] = optimizeStep.moved_cells[-1], optimizeStep.moved_cells[i]
                        self.illegal_cells.append(optimizeStep.moved_cells.pop())
                    else:
                        i += 1

                # all cell are legal
                if len(self.illegal_cells) == 0:    
                    self.detail_status = DetailStatus.SHOWRESULT
            case DetailStatus.SHOWRESULT:
                # all cell are legal, setup all rest cells
                for cell_name, (cell_x, cell_y) in optimizeStep.moved_cells:
                    cell = self.cells[cell_name]
                    cell.x = cell_x
                    cell.y = cell_y
                    cell.color = LEGAL_COLOR
                    self.canva.setCellPosition(cell, -0.7)
                    self.canva.setCellColor(cell)
                    self.prev_moved_cells.append(cell)
                self.canva.merge_cell_init = False # don't draw current cell

                # reset color and z index for prev moved cell
                for cell in self.prev_moved_cells:
                    cell.color = MERGE_COLOR if cell.is_merge else NOTFIX_COLOR
                    self.canva.setCellColor(cell)

                    z = -0.9 if cell.is_merge else 1.
                    self.canva.setCellPosition(cell, z) # use to reset z
                self.prev_moved_cells = []

                self.detail_status = DetailStatus.REMOVE
        self.canva.updateAllBuffer()
        return self.detail_status == DetailStatus.REMOVE

class Visualizer:
    def __init__(self, lg_file: str, opt_file: str, post_file: str, output_file: str, display: bool, detail: bool, args):
        self.start_time = time.time()
        self.board = Board(display)
        self.board.parser(lg_file)

        self.optimize_cases: list[OptimizeStep] = []
        self.optimizeStepInit(opt_file, post_file)

        self.detail = detail

        self.video_out = False
        if output_file:
            self.video_out = True
            self.process = (
                ffmpeg
                .input('pipe:0', format='rawvideo', pix_fmt='rgb24', s=f'{RESOLUTION[0]}x{RESOLUTION[1]}', framerate=args.framerate)
                .filter('vflip') # vertical flip to convert opengl coordinate to normal coordinate
                .output(output_file, pix_fmt=args.pix_fmt, vcodec=args.vcodec, crf=args.crf, preset=args.preset)
                .overwrite_output() # override output if exist
                .run_async(pipe_stdin=True) #input from stdin
            )

        self.display = display

        if not self.display:
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self.board.canva.fbo)

        self.n_step = 0

        # draw first frame
        if self.display:
            self.board.canva.display()
        else:
            self.board.canva.draw()

    # combine post and opt data
    def optimizeStepInit(self, opt_file, post_file):
        with open(opt_file, "r") as file:
            opt_lines = file.read().splitlines()
        with open(post_file, "r") as file:
            post_lines = file.read().splitlines()

        post_line_idx = 0
        for line in opt_lines:
            parts = line.split(' ')

            # <merge list> --> <name> <x> <y> <width> <height>
            #    1:-6      -6    -5   -4   -3   -2       -1
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

            self.optimize_cases.append(OptimizeStep(removed_cells, x, y, 
                                                    Cell(name, original_x, original_y, width, height, False, True, -1), moved_cells))
            
    # https://stackoverflow.com/questions/41126090/how-to-write-pyopengl-in-to-jpg-image
    def captureFrame(self):
        if not self.display:
            glReadBuffer(GL_COLOR_ATTACHMENT0)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        pixels = glReadPixels(0, 0, *RESOLUTION, GL_RGB, GL_UNSIGNED_BYTE)
        self.process.stdin.write(pixels)
    
    # return finish or not
    def step(self):
        if self.video_out:
            self.captureFrame()

        if self.detail:
            finish = self.board.detailStep(self.optimize_cases[self.n_step])
        else:
            finish = self.board.step(self.optimize_cases[self.n_step])
        if finish:
            # move to next cases
            self.n_step += 1
            if self.n_step == len(self.optimize_cases):
                self.terminate()
                return True

        # swap buffer only if display
        if self.display:
            self.board.canva.display()
        else:   
            self.board.canva.draw()
        return False

    def terminate(self):
        self.process.stdin.close()
        self.process.wait() 
        print(f"visualization finish, cost: {time.time() - self.start_time} secs")
        if self.display:
            glfw.set_window_should_close(self.board.canva.window, True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-lg',     type=str, required=True, help="lg file")
    parser.add_argument('-opt',    type=str, required=True, help="opt file")
    parser.add_argument('-postlg', type=str, required=True, help="post file")
    parser.add_argument('-o', type=str, help="output file")
    parser.add_argument('-display', action='store_true', help="render screen")
    parser.add_argument('-detail', action='store_true', help="show process of every cell in legalization")
    # ffmpeg format
    parser.add_argument('-pix_fmt', type=str, default='yuv444p', help="ffmpeg option, pixel format")
    parser.add_argument('-framerate', type=int, default=60, help="ffmpeg option, fps")
    parser.add_argument('-vcodec', type=str, default='h264', help="ffmpeg option, encoder to use")
    parser.add_argument('-preset', type=str, default='veryfast', 
                        help="""ffmpeg option, slower preset will provide better compression (compression is quality per filesize).
                             available value: ultrafast, superfast, veryfast, faster, fast, medium(default in ffmpeg), slow, slower, veryslow
                             """)
    parser.add_argument('-crf', type=int, default=18, 
                        help="""ffmpeg option, the qulaity of output, lower value means higher quality. 
                                0 for lossless, 18 for visually lossless in h264. 
                                ffmpeg default value is 23 for h264, 28 for h265""")
    args = parser.parse_args()   
    lg_file = args.lg 
    opt_file = args.opt
    post_file = args.postlg
    output_file = args.o
    detail = args.detail

    if detail:
        NOTFIX_COLOR = DETAIL_NOTFIX_COLOR
        FIX_COLOR = DETAIL_FIX_COLOR

    display = True if args.display else False
    visualizer = Visualizer(lg_file, opt_file, post_file, output_file, display, detail, args)

    if display:
        while not glfw.window_should_close(visualizer.board.canva.window):
            visualizer.step()         # Update state
            glfw.poll_events()  # Process events
    else:
        while not visualizer.step():
            pass
