import os
import re
from typing import List
import matplotlib.pyplot as plt
import numpy as np
import sys
#import cv2
from matplotlib.colors import LinearSegmentedColormap

argv = 5000
# 檢查是否有提供足夠的參數
if len(sys.argv) < 2:
    print("請提供一個整數作為參數")
    sys.exit(1)

# 取得命令列參數
try:
    argv = int(sys.argv[1])  # 將參數轉換為整數
    #print(f"取得的整數是: {number}")
except ValueError:
    print("提供的參數不是有效的整數")
    sys.exit(1)

print("argv = ", argv)
#print(argv)
index = 1

if argv == 5000: 
    index = 1
elif argv == 16900:
    index = 0
elif argv == 100:
    index = 2
elif argv == 7000:
    index = 3
else:
    print("請提供有效的參數")

print("index = ", index)

filename = ["./tc/testcase1_16900", "./tc/testcase1_ALL0_5000", "./tc/testcase2_100", "./tc/testcase1_MBFF_LIB_7000"]

colors = [(1, 1, 1), (0.7, 0.7, 0.7), (0.5, 0.5, 0.5), (0.3, 0.3, 0.3), (0, 0, 0)]
positions = [0.0, 0.5, 0.7, 0.85, 1.0]  # 對應區間：平緩(0.0-0.5)、次陡降(0.5-0.7)、陡降(0.7-1.0)
custom_cmap = LinearSegmentedColormap.from_list("custom_greys", list(zip(positions, colors)))

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


components = []
banking_cells = []
merged_ff_updates = []
placement_rows = []


# Function to read and parse the lg file
def read_lg_file(file_path: str):
    alpha = 0
    beta = 0
    die_size = None
    #components = []
    #placement_rows = []

    if not os.path.exists(file_path):
        print("File not found.")
        return

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
            _, x, y, site_width, site_height, num_sites = line.split()
            placement_rows.append(PlacementRow(int(x), int(y), int(site_width), int(site_height), int(num_sites)))
        # Parse Component
        else:
            tokens = line.split()
            name, x, y, w, h, is_fixed_str = tokens
            is_fixed = (is_fixed_str == "FIX")
            components.append(Component(name, int(x), int(y), int(w), int(h), is_fixed))

    # Calculate and print the bounding box of the placement rows
    '''
    if placement_rows:
        min_x = min(row.x for row in placement_rows)
        min_y = min(row.y for row in placement_rows)
        max_x = max(row.x + row.site_width * row.num_sites for row in placement_rows)
        max_y = placement_rows[-1].y + placement_rows[-1].site_height

        # Split the bounding box into 10x10 grid and write to file
        grid_points = []
        x_step = (max_x - min_x) / 10.0
        y_step = (max_y - min_y) / 10.0
        for j in range(10):  # Iterate from bottom to top for y
            for i in range(10):  # Iterate from left to right for x
                grid_points.append((min_x + i * x_step, min_y + j * y_step))

        with open(filename[index] + ".grid", "w") as grid_file:
            for point in grid_points:
                grid_file.write(f"{point[0]} {point[1]}\n")

    # Calculate area utilization of components within the 10x10 grid
    grid_utilization = [[0.0 for _ in range(10)] for _ in range(10)]
    grid_area = x_step * y_step
    for component in components:
        for j in range(10):  # Iterate from bottom to top for y
            for i in range(10):  # Iterate from left to right for x
                grid_min_x = min_x + i * x_step
                grid_max_x = grid_min_x + x_step
                grid_min_y = min_y + j * y_step
                grid_max_y = grid_min_y + y_step

                # Calculate overlap area between component and current grid cell
                overlap_min_x = max(component.x, grid_min_x)
                overlap_max_x = min(component.x + component.w, grid_max_x)
                overlap_min_y = max(component.y, grid_min_y)
                overlap_max_y = min(component.y + component.h, grid_max_y)

                if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                    overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                    grid_utilization[j][i] += overlap_area / grid_area

    # Write grid utilization to file
    with open(filename[index] + ".util", "w") as util_file:
        for row in grid_utilization[::-1]:  # Reverse rows to write from bottom to top
            util_file.write(" ".join(map(str, row)) + "\n")


    # Create a heatmap using matplotlib
    plt.figure(figsize=(8, 6))
    utilization_array = np.array(grid_utilization)
    plt.imshow(utilization_array, cmap=custom_cmap, interpolation="nearest", origin="lower", vmin=0, vmax=1)
    plt.colorbar(label="Utilization")
    plt.title("Grid Utilization Heatmap")
    plt.xlabel("Grid X Index")
    plt.ylabel("Grid Y Index")
    plt.xticks(np.arange(10))
    plt.yticks(np.arange(10))

    for j in range(10):
            for i in range(10):
                plt.text(i, j, f"{utilization_array[j, i] * 100:.0f}", ha='center', va='center', color='black')


    plt.savefig(filename[index] + ".png")
    plt.close()
    '''

# Function to read and parse the opt file
def read_opt_file(file_path: str):
    #banking_cells = []

    if not os.path.exists(file_path):
        print("File not found.")
        return

    with open(file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.strip()
        if not line or not line.startswith("Banking_Cell:"):
            continue

        # Parse Banking_Cell line
        line = line.replace("Banking_Cell:", "").strip()
        ff_list_part, merged_part = line.split("-->")
        ff_list = ff_list_part.split()
        merged_tokens = merged_part.split()
        merged_name = merged_tokens[0]
        x, y, w, h = map(int, merged_tokens[1:])
        banking_cells.append(BankingCell(ff_list, merged_name, x, y, w, h))

    # Print the parsed data
    #print("BankingCells (first 5):")
    #for cell in banking_cells[:5]:
    #    print(f"  {cell}")

    return banking_cells

# Function to read and parse the post file
def read_post_file(file_path: str, banking_cells: List[BankingCell]):
    #merged_ff_updates = []

    if not os.path.exists(file_path):
        print("File not found.")
        return

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

        # Assign newFF from corresponding BankingCell
        new_ff = banking_cells[len(merged_ff_updates)].merged_name if len(merged_ff_updates) < len(banking_cells) else ""
        merged_ff_updates.append(MergedFFUpdate(x, y, moved_cells, new_ff))

    # Print the parsed data
    #print("MergedFFUpdates (first 5):")
    #for update in merged_ff_updates[:5]:
    #    print(f"  {update}")

# Example usage if testcase1_ALL0_5000.lg, testcase1_ALL0_5000.opt, and testcase1_ALL0_5000_post.lg are in the current directory

read_lg_file(filename[index] + ".lg")
banking_cells = read_opt_file(filename[index] + ".opt")
read_post_file(filename[index] + "_post.lg", banking_cells)


for k, cell in enumerate(banking_cells):
    #print(i)
    # 刪除 banked cells
    for delname in cell.ff_list:
        components = [comp for comp in components if comp.name != delname]  # 移除 name 與 delname 匹配的元件
        #print(f"Deleted: {delname}")

    # 加入 new ff
    if k < len(merged_ff_updates):
        components.append(Component(cell.merged_name, merged_ff_updates[k].x, merged_ff_updates[k].y, cell.w, cell.h, False))     #warning
    #print(f"Added: {cell.merged_name} at ({merged_ff_updates[k].x}, {merged_ff_updates[k].y}) with size ({cell.w}, {cell.h})")
    #print(f"Components: {len(components)}")

    # 移動 ff
    if k < len(merged_ff_updates):
        for moved in merged_ff_updates[k].moved_cells:
            for comp in components:
                if comp.name == moved.name:
                    comp.x = moved.x
                    comp.y = moved.y


    # 計算 bounding box
    #if placement_rows:
    min_x = min(row.x for row in placement_rows)
    min_y = min(row.y for row in placement_rows)
    max_x = max(row.x + row.site_width * row.num_sites for row in placement_rows)
    max_y = placement_rows[-1].y + placement_rows[-1].site_height
    #print(f"Bounding box: ({min_x}, {min_y}), ({max_x}, {max_y})")

    x_step = (max_x - min_x) / 10.0
    y_step = (max_y - min_y) / 10.0
    #print(f"Grid division: x_step={x_step}, y_step={y_step}")

    total_width = max_x - min_x
    total_height = max_y - min_y
    if not np.isclose(total_width, x_step * 10) or not np.isclose(total_height, y_step * 10):
        print(f"Grid division mismatch: total_width={total_width}, total_height={total_height}")

        
    if(k%1000 == 0 or k == len(banking_cells) - 1):
        # 初始化 grid utilization
        grid_utilization = [[0.0 for _ in range(10)] for _ in range(10)]
        grid_area = x_step * y_step

        for component in components:
            if component.x + component.w > max_x or component.y + component.h > max_y:
                print(f"Component {component.name} exceeds bounds: x+w={component.x + component.w}, y+h={component.y + component.h}")

            for j in range(10):
                for i in range(10):
                    grid_min_x = min_x + i * x_step
                    grid_max_x = grid_min_x + x_step
                    grid_min_y = min_y + j * y_step
                    grid_max_y = grid_min_y + y_step

                    overlap_min_x = max(component.x, grid_min_x)
                    overlap_max_x = min(component.x + component.w, grid_max_x)
                    overlap_min_y = max(component.y, grid_min_y)
                    overlap_max_y = min(component.y + component.h, grid_max_y)


                    if overlap_min_x <= overlap_max_x and overlap_min_y <= overlap_max_y:
                        overlap_area = (overlap_max_x - overlap_min_x) * (overlap_max_y - overlap_min_y)
                        grid_utilization[j][i] += overlap_area / grid_area

        #  畫圖並將圖片轉為 NumPy 陣列
        fig, ax = plt.subplots(figsize=(8, 6))
        utilization_array = np.array(grid_utilization)
        cax = ax.imshow(utilization_array, cmap=custom_cmap, interpolation="nearest", origin="lower", vmin=0, vmax=1)
        ax.set_title("Grid Utilization Heatmap")
        ax.set_xlabel("Grid X Index")
        ax.set_ylabel("Grid Y Index")
        fig.colorbar(cax, ax=ax, label="Utilization")

        # 加入每格的數值標籤
        for j in range(10):
            for i in range(10):
                ax.text(i, j, f"{utilization_array[j, i] * 100:.0f}", ha='center', va='center', color='black')

        # 儲存圖片，檔名包含流水號（從1開始）
        base = os.path.basename(filename[index])  # 獲取檔名
        
        argvstr = str(argv)
        fn = f"./{argvstr}/{base}_{k//1000}.png"  # 使用整數除法

        fig.savefig(fn, dpi=300)

        print(f"Saved: {fn}")

        # 關閉圖表以節省資源
        plt.close(fig)