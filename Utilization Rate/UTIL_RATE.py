import os
import re
from typing import List
import matplotlib.pyplot as plt
import numpy as np
#import cv2
import argparse
from matplotlib.colors import LinearSegmentedColormap
import math
import imageio
import io

from PIL import Image

# Component class to hold information about each component
class Component:
    def __init__(self, name, x, y, w, h, is_fixed):
        self.name = name
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.is_fixed = is_fixed

    def __repr__(self):
        return f"Component(name={self.name}, x={self.x}, y={self.y}, w={self.w}, h={self.h}, is_fixed={self.is_fixed})"

# PlacementRow class to hold information about each placement row
class PlacementRow:
    def __init__(self, x, y, site_width, site_height, num_sites):
        self.x = x
        self.y = y
        self.site_width = site_width
        self.site_height = site_height
        self.num_sites = num_sites

    def __repr__(self):
        return f"PlacementRow(x={self.x}, y={self.y}, site_width={self.site_width}, site_height={self.site_height}, num_sites={self.num_sites})"

# BankingCell class to hold information about merged flip-flops
class BankingCell:
    def __init__(self, ff_list, merged_name, x, y, w, h):
        self.ff_list = ff_list
        self.merged_name = merged_name
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __repr__(self):
        return f"BankingCell(ff_list={self.ff_list}, merged_name={self.merged_name}, x={self.x}, y={self.y}, w={self.w}, h={self.h})"

# MovedCell class to hold information about moved cells
class MovedCell:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

    def __repr__(self):
        return f"MovedCell(name={self.name}, x={self.x}, y={self.y})"

# MergedFFUpdate class to hold information about merged flip-flop updates
class MergedFFUpdate:
    def __init__(self, x, y, moved_cells, new_ff):
        self.x = x
        self.y = y
        self.moved_cells = moved_cells
        self.new_ff = new_ff

    def __repr__(self):
        return f"MergedFFUpdate(x={self.x}, y={self.y}, moved_cells={self.moved_cells}, new_ff={self.new_ff})"


# Function to read and parse the lg file
def read_lg_file(file_path: str, placement_rows: List[PlacementRow], components: List[Component]) -> None:
    """
    Parse the LG file and populate the placement_rows and components lists.
    
    Args:
        file_path (str): Path to the LG file.
        placement_rows (List[PlacementRow]): List to populate placement row data.
        components (List[Component]): List to populate component data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse Alpha and Beta values
        if line.startswith("Alpha"):
            _, alpha_value = line.split()
            alpha = int(alpha_value)
        elif line.startswith("Beta"):
            _, beta_value = line.split()
            beta = int(beta_value)
        # Parse DieSize
        elif line.startswith("DieSize"):
            die_size = list(map(int, re.findall(r"\d+", line)))
        # Parse PlacementRows
        elif line.startswith("PlacementRows"):
            try:
                _, x, y, site_width, site_height, num_sites = line.split()
                placement_rows.append(PlacementRow(int(x), int(y), int(site_width), int(site_height), int(num_sites)))
            except ValueError:
                print(f"Skipping malformed PlacementRows line: {line}")
        # Parse Component
        else:
            tokens = line.split()
            if len(tokens) != 6:
                print(f"Skipping malformed Component line: {line}")
                continue
            name, x, y, w, h, is_fixed_str = tokens
            is_fixed = (is_fixed_str == "FIX")
            components.append(Component(name, int(x), int(y), int(w), int(h), is_fixed))


# Function to read and parse the opt file

def read_opt_file(file_path: str, banking_cells: List[BankingCell]) -> None:
    """
    Parse OPT file and populate the banking_cells list.

    Args:
        file_path (str): Path to the OPT file.
        banking_cells (List[BankingCell]): List to populate banking cell data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if not line or not line.startswith("Banking_Cell:"):
            continue

        # Parse Banking_Cell line
        try:
            line = line.replace("Banking_Cell:", "").strip()
            ff_list_part, merged_part = line.split("-->")
            ff_list = ff_list_part.split()
            merged_tokens = merged_part.split()
            merged_name = merged_tokens[0]
            x, y, w, h = map(int, merged_tokens[1:])
            banking_cells.append(BankingCell(ff_list, merged_name, x, y, w, h))
        except ValueError:
            print(f"Skipping malformed Banking_Cell line: {line}")

def read_post_file(file_path: str, banking_cells: List[BankingCell], merged_ff_updates: List[MergedFFUpdate]) -> None:
    """
    Parse POST file and populate the merged_ff_updates list.

    Args:
        file_path (str): Path to the POST file.
        banking_cells (List[BankingCell]): List of banking cells to match new FFs.
        merged_ff_updates (List[MergedFFUpdate]): List to populate merged FF updates.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r") as file:
        lines = file.readlines()

    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue

        # Parse merged ff coordinates
        x, y = map(int, line.split())
        idx += 1

        # Parse number of moved cells
        num_moved_cells = int(lines[idx].strip())
        idx += 1

        moved_cells = []
        for _ in range(num_moved_cells):
            cell_line = lines[idx].strip()
            name, cell_x, cell_y = cell_line.split()
            moved_cells.append(MovedCell(name, int(cell_x), int(cell_y)))
            idx += 1

        # Assign new FF from corresponding BankingCell
        if len(merged_ff_updates) < len(banking_cells):
            new_ff = banking_cells[len(merged_ff_updates)].merged_name
        else:
            new_ff = ""

        merged_ff_updates.append(MergedFFUpdate(x, y, moved_cells, new_ff))

def parse_arguments():
    """Parse command-line arguments using argparse."""
    parser = argparse.ArgumentParser(description="Process LG, OPT, and POST files for placement optimization.")
    parser.add_argument("lgfile", type=str, help="Path to the LG file.")
    parser.add_argument("optfile", type=str, help="Path to the OPT file.")
    parser.add_argument("postfile", type=str, help="Path to the POST file.")
    parser.add_argument("utilGraphDir", type=str, help="Directory to save utilization heatmaps.")
    parser.add_argument("xStepNum", type=int, help="Number of grid steps in X direction.")
    parser.add_argument("yStepNum", type=int, help="Number of grid steps in Y direction.")
    parser.add_argument("stepCut", type=int, help="Step interval for saving intermediate heatmaps.")
    return parser.parse_args()

''' 
### for gif
def remove_transparency(image_folder: str, background_color=(255, 255, 255)):
    for file in sorted(os.listdir(image_folder)):
        if file.lower().endswith(".png"):  # Use .lower() to ensure case-insensitive match
            img_path = os.path.join(image_folder, file)
            img = Image.open(img_path)
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, background_color)
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                background.save(img_path)
                print(f"Removed transparency from {file}")

def resize_images_to_uniform_size(image_folder: str, target_size: tuple):
    """
    Resize all images in the folder to the target size.

    Args:
        image_folder (str): Directory containing images.
        target_size (tuple): Target size as (width, height).
    """
    for file in sorted(os.listdir(image_folder)):
        if file.lower().endswith(".png"):  # Ensure only .png files are processed
            img_path = os.path.join(image_folder, file)
            img = Image.open(img_path)
            resized_img = img.resize(target_size, resample=Image.Resampling.LANCZOS)
            resized_img.save(img_path)
            print(f"Resized {file} to {target_size}")


def check_image_shapes(image_folder: str):
    """
    Check and print the dimensions and mode of PNG images in the folder.
    """
    for file in sorted(os.listdir(image_folder)):
        if file.lower().endswith(".png"):  # Ensure only .png files are processed
            img = Image.open(os.path.join(image_folder, file))
            print(f"Image: {file}, Size: {img.size}, Mode: {img.mode}")


def create_gif(image_folder: str, gif_filename: str, duration: float):
    """
    Create a GIF from a sequence of PNG images in a specified folder.

    Args:
        image_folder (str): Path to the folder containing images.
        gif_filename (str): Output GIF file path.
        duration (float): Duration of each frame in seconds.
    """
    # Collect only .png files, sorted by filename
    images = sorted([os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.lower().endswith(".png")])

    # Read and save images as a GIF
    gif_images = [imageio.imread(img) for img in images]
    imageio.mimsave(gif_filename, gif_images, duration=duration)
    print(f"GIF saved to {gif_filename}")

'''
###

import io
from PIL import Image

def main():
    # 灰階的深淺降低幅度
    colors = [(1, 1, 1), (1, 1, 0), (1, 0, 0)]  # 白色 -> 黃色 -> 紅色
    positions = [0.0, 0.5, 1.0]  # 對應位置
    custom_cmap = LinearSegmentedColormap.from_list("custom_red_yellow_white", list(zip(positions, colors)))

    # Parse command-line arguments
    args = parse_arguments()
    lgfile = args.lgfile
    optfile = args.optfile
    postfile = args.postfile
    utilGraphDir = args.utilGraphDir  # For saving final GIF
    xStepNum = args.xStepNum
    yStepNum = args.yStepNum
    stepCut = args.stepCut

    print("xStepNum = ", xStepNum)
    print("yStepNum = ", yStepNum)
    print("stepCut = ", stepCut)

    components = []
    banking_cells = []
    merged_ff_updates = []
    placement_rows = []

    # Read input files
    print(f"Reading LG file: {lgfile}")
    read_lg_file(lgfile, placement_rows, components)

    print(f"Reading OPT file: {optfile}")
    read_opt_file(optfile, banking_cells)

    print(f"Reading POST file: {postfile}")
    read_post_file(postfile, banking_cells, merged_ff_updates)

    # Calculate bounding box
    min_x = min(row.x for row in placement_rows)
    min_y = min(row.y for row in placement_rows)
    max_x = max(row.x + row.site_width * row.num_sites for row in placement_rows)
    max_y = placement_rows[-1].y + placement_rows[-1].site_height
    x_step = (max_x - min_x) / xStepNum
    y_step = (max_y - min_y) / yStepNum

    # Initialize grid utilization
    grid_utilization = [[0.0 for _ in range(xStepNum)] for _ in range(yStepNum)]
    grid_area = x_step * y_step

    # Create a list to store frames for the GIF
    gif_frames = []

    # Pre-opt utilization
    for component in components:
        if component.x + component.w > max_x or component.y + component.h > max_y:
            print(f"Component {component.name} exceeds bounds: x+w={component.x + component.w}, y+h={component.y + component.h}")
        
        startXidx = math.floor((component.x - min_x) / x_step)
        endXidx = math.ceil((component.x + component.w - min_x) / x_step)
        startYidx = math.floor((component.y - min_y) / y_step)
        endYidx = math.ceil((component.y + component.h - min_y) / y_step)

        for j in range(startYidx, endYidx):
            grid_min_y = min_y + j * y_step
            grid_max_y = grid_min_y + y_step
            for i in range(startXidx, endXidx):
                grid_min_x = min_x + i * x_step
                grid_max_x = grid_min_x + x_step

                overlap_min_x = max(component.x, grid_min_x)
                overlap_max_x = min(component.x + component.w, grid_max_x)
                overlap_min_y = max(component.y, grid_min_y)
                overlap_max_y = min(component.y + component.h, grid_max_y)

                if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                    overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                    grid_utilization[j][i] += overlap_area / grid_area

    # Add initial heatmap to GIF frames
    fig, ax = plt.subplots(figsize=(8, 6))
    utilization_array = np.array(grid_utilization)
    vmin, vmax = utilization_array.min(), utilization_array.max()
    cax = ax.imshow(utilization_array, cmap=custom_cmap, interpolation="nearest", origin="lower", vmin=vmin, vmax=vmax)
    #ax.set_title("Grid Utilization Heatmap")
    ax.set_title(f"Grid Utilization Heatmap (Step {-1}, initial log layout)")
    ax.set_xlabel("Grid X Index")
    ax.set_ylabel("Grid Y Index")
    fig.colorbar(cax, ax=ax, label="Utilization")
    for j in range(yStepNum):
            for i in range(xStepNum):
                ax.text(i, j, f"{utilization_array[j, i] * 100:.0f}", ha='center', va='center', color='black')

    #print(utilization_array)
    #plt.show()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    gif_frames.append(Image.open(buf).convert("RGB"))  # Convert to ensure consistency
    buf.close()
    plt.close(fig)

    # Optimization steps
    for k, cell in enumerate(banking_cells):
        # Update grid utilization for deleted and moved cells
        # ... (retain your existing logic for grid updates)
        # 刪除 banked cells
        for delname in cell.ff_list:
            # 刪除利用率
            for compo in components:
                if compo.name == delname:
                    startXidx = math.floor((compo.x-min_x)/x_step) #小
                    endXidx = math.ceil((compo.x + compo.w-min_x)/x_step) # 大
                    startYidx = math.floor((compo.y-min_y)/y_step)
                    endYidx = math.ceil((compo.y + compo.h-min_y)/y_step)
                    for j in range(startYidx, endYidx):
                        grid_min_y = min_y + j * y_step
                        grid_max_y = grid_min_y + y_step
                        for i in range(startXidx, endXidx):
                            grid_min_x = min_x + i * x_step
                            grid_max_x = grid_min_x + x_step

                            overlap_min_x = max(compo.x, grid_min_x)
                            overlap_max_x = min(compo.x + compo.w, grid_max_x)
                            overlap_min_y = max(compo.y, grid_min_y)
                            overlap_max_y = min(compo.y + compo.h, grid_max_y)

                            if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                                overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                                grid_utilization[j][i] -= overlap_area / grid_area # 改為 -=
                                
                                #print(f"Delete {delname} at ({compo.x}, {compo.y})")
                    #刪除他
                    components.remove(compo)
                    break
                

        # 加入 new ff
        if k < len(merged_ff_updates):
            components.append(Component(cell.merged_name, merged_ff_updates[k].x, merged_ff_updates[k].y, cell.w, cell.h, False))
            # 加入他的利用率
            startXidx = math.floor((merged_ff_updates[k].x-min_x)/x_step) #小
            endXidx = math.ceil((merged_ff_updates[k].x + cell.w-min_x)/x_step) # 大
            startYidx = math.floor((merged_ff_updates[k].y-min_y)/y_step)
            endYidx = math.ceil((merged_ff_updates[k].y + cell.h-min_y)/y_step)
            for j in range(startYidx, endYidx):
                grid_min_y = min_y + j * y_step
                grid_max_y = grid_min_y + y_step
                for i in range(startXidx, endXidx):
                    grid_min_x = min_x + i * x_step
                    grid_max_x = grid_min_x + x_step

                    overlap_min_x = max(merged_ff_updates[k].x, grid_min_x)
                    overlap_max_x = min(merged_ff_updates[k].x + cell.w, grid_max_x)
                    overlap_min_y = max(merged_ff_updates[k].y, grid_min_y)
                    overlap_max_y = min(merged_ff_updates[k].y + cell.h, grid_max_y)

                    if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                        overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                        grid_utilization[j][i] += overlap_area / grid_area # 改為 +=

                        #print (f"Add {cell.merged_name} at ({merged_ff_updates[k].x}, {merged_ff_updates[k].y})")

        # 移動 ff
        if k < len(merged_ff_updates):
            for moved in merged_ff_updates[k].moved_cells:
                for comp in components:
                    if comp.name == moved.name:
                        #刪除利用率
                        startXidx = math.floor((comp.x-min_x)/x_step) #小
                        endXidx = math.ceil((comp.x + comp.w-min_x)/x_step) # 大
                        startYidx = math.floor((comp.y-min_y)/y_step)
                        endYidx = math.ceil((comp.y + comp.h-min_y)/y_step)
                        for j in range(startYidx, endYidx):
                            grid_min_y = min_y + j * y_step
                            grid_max_y = grid_min_y + y_step
                            for i in range(startXidx, endXidx):
                                grid_min_x = min_x + i * x_step
                                grid_max_x = grid_min_x + x_step

                                overlap_min_x = max(comp.x, grid_min_x)
                                overlap_max_x = min(comp.x + comp.w, grid_max_x)
                                overlap_min_y = max(comp.y, grid_min_y)
                                overlap_max_y = min(comp.y + comp.h, grid_max_y)

                                if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                                    overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                                    grid_utilization[j][i] -= overlap_area / grid_area # 改為 -=
                                #print(f"Move - {moved.name} from ({comp.x}, {comp.y}) to ({moved.x}, {moved.y})")
                        #移動
                        comp.x = moved.x
                        comp.y = moved.y
                        #加入利用率
                        startXidx = math.floor((comp.x-min_x)/x_step) #小
                        endXidx = math.ceil((comp.x + comp.w-min_x)/x_step) # 大
                        startYidx = math.floor((comp.y-min_y)/y_step)
                        endYidx = math.ceil((comp.y + comp.h-min_y)/y_step)
                        for j in range(startYidx, endYidx):
                            grid_min_y = min_y + j * y_step
                            grid_max_y = grid_min_y + y_step
                            for i in range(startXidx, endXidx):
                                grid_min_x = min_x + i * x_step
                                grid_max_x = grid_min_x + x_step

                                overlap_min_x = max(comp.x, grid_min_x)
                                overlap_max_x = min(comp.x + compo.w, grid_max_x)
                                overlap_min_y = max(comp.y, grid_min_y)
                                overlap_max_y = min(comp.y + comp.h, grid_max_y)

                                if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                                    overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                                    grid_utilization[j][i] += overlap_area / grid_area # 改為 +=
                                    #print(f"Move + {moved.name} from ({comp.x}, {comp.y}) to ({moved.x}, {moved.y})")
                        
                        break
        
        # Add intermediate heatmap to GIF frames
        if (k % stepCut == 0 and k > 0) or k == len(banking_cells) - 1:
            fig, ax = plt.subplots(figsize=(8, 6))
            utilization_array = np.array(grid_utilization)
            vmin, vmax = utilization_array.min(), utilization_array.max()
            cax = ax.imshow(utilization_array, cmap=custom_cmap, interpolation="nearest", origin="lower", vmin=0, vmax=1)
            #ax.set_title("Grid Utilization Heatmap")
            ax.set_title(f"Grid Utilization Heatmap (Step {k})")
            ax.set_xlabel("Grid X Index")
            ax.set_ylabel("Grid Y Index")
            fig.colorbar(cax, ax=ax, label="Utilization")
            for j in range(yStepNum):
                for i in range(xStepNum):
                    ax.text(i, j, f"{utilization_array[j, i] * 100:.0f}", ha='center', va='center', color='black')

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            gif_frames.append(Image.open(buf).convert("RGB"))  # Convert to ensure consistency
            buf.close()
            plt.close(fig)

    # Save the GIF
    gif_output_path = os.path.join(utilGraphDir, "output.gif")
    gif_frames[0].save(
        gif_output_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=200,  # Duration in milliseconds
        loop=0
    )
    print(f"GIF saved to {gif_output_path}")




if __name__ == "__main__":
    main()
