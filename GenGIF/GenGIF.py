import argparse
import matplotlib.pyplot as plt
from PIL import Image

# 文件解析功能
def parse_files(lg_file, opt_file, postlg_file):
    layout_data = parse_lg(lg_file)
    opt_steps = parse_opt(opt_file)
    post_layout = parse_postlg(postlg_file)
    return layout_data, opt_steps, post_layout

def parse_lg(lg_file):
    with open(lg_file, "r") as f:
        lines = f.readlines()
    layout = {"die_size": [], "cells": [], "rows": []}
    for line in lines:
        if line.startswith("DieSize"):
            layout["die_size"] = list(map(int, line.split()[1:]))
        elif line.startswith("FF_") or line.startswith("Gate_") or line.startswith("C4"):
            parts = line.split()
            layout["cells"].append({
                "name": parts[0],
                "x": int(parts[1]),
                "y": int(parts[2]),
                "w": int(parts[3]),
                "h": int(parts[4]),
                "fixed": parts[5] == "FIX"
            })
        elif line.startswith("PlacementRows"):
            layout["rows"].append(list(map(int, line.split()[1:])))
    return layout

def parse_opt(opt_file):
    with open(opt_file, "r") as f:
        lines = f.readlines()
    steps = []
    for line in lines:
        if line.startswith("Banking_Cell"):
            parts = line.split(":")[1].strip().split("-->")
            inputs = parts[0].split()
            output, *coords = parts[1].split()
            steps.append({
                "inputs": inputs,
                "output": output,
                "x": int(coords[0]),
                "y": int(coords[1]),
                "w": int(coords[2]),
                "h": int(coords[3])
            })
    return steps

def parse_postlg(postlg_file):
    with open(postlg_file, "r") as f:
        lines = f.readlines()
    positions = []
    moved_cells = []
    i = 0
    while i < len(lines):
        merged_ff = list(map(int, lines[i].split()))
        positions.append({"x": merged_ff[0], "y": merged_ff[1]})
        i += 1
        num_of_cells = int(lines[i].strip())
        i += 1
        if num_of_cells > 0:
            for _ in range(num_of_cells):
                cell_info = lines[i].split()
                moved_cells.append({
                    "name": cell_info[0],
                    "x": int(cell_info[1]),
                    "y": int(cell_info[2])
                })
                i += 1
    return positions, moved_cells

# 可視化功能
def generate_animation(frames, output_file):
    frames[0].save(
        output_file,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=500
    )

def visualize_steps(layout_data, opt_steps, post_layout):
    frames = []
    current_cells = layout_data["cells"].copy()
    frames.append(draw_layout(layout_data, current_cells))
    for step in opt_steps:
        current_cells = [cell for cell in current_cells if cell["name"] not in step["inputs"]]
        current_cells.append({
            "name": step["output"],
            "x": step["x"],
            "y": step["y"],
            "w": step["w"],
            "h": step["h"],
            "fixed": False
        })
        frames.append(draw_layout(layout_data, current_cells))
    frames.append(draw_layout(layout_data, current_cells, final=True))
    return frames

def draw_layout(layout_data, cells, final=False):
    fig, ax = plt.subplots()
    die_size = layout_data["die_size"]
    ax.set_xlim(die_size[0], die_size[2])
    ax.set_ylim(die_size[1], die_size[3])
    for cell in cells:
        draw_cell(ax, cell, color="blue" if not cell["fixed"] else "red")
    if final:
        ax.set_title("Final Layout")
    else:
        ax.set_title("Intermediate Layout")
    fig.canvas.draw()
    image = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    plt.close(fig)
    return image

def draw_cell(ax, cell, color="blue"):
    rect = plt.Rectangle(
        (cell["x"], cell["y"]),
        cell["w"], cell["h"],
        edgecolor="black",
        facecolor=color,
        alpha=0.7
    )
    ax.add_patch(rect)
    ax.text(
        cell["x"] + cell["w"] / 2,
        cell["y"] + cell["h"] / 2,
        cell["name"],
        ha="center",
        va="center",
        fontsize=8
    )

# 主程式
def main():
    parser = argparse.ArgumentParser(description="Generate GIF/MP4 for layout optimization steps.")
    parser.add_argument("-lg", required=True, help="Input .lg file.")
    parser.add_argument("-opt", required=True, help="Input .opt file.")
    parser.add_argument("-postlg", required=True, help="Input .postlg file.")
    parser.add_argument("-o", required=True, help="Output GIF/MP4 file.")
    args = parser.parse_args()
    layout_data, opt_steps, post_layout = parse_files(args.lg, args.opt, args.postlg)
    frames = visualize_steps(layout_data, opt_steps, post_layout)
    generate_animation(frames, args.o)

if __name__ == "__main__":
    main()
