import argparse
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

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
def generate_mp4(frames, output_file):
    metadata = {'title': 'Layout Optimization', 'artist': 'Matplotlib'}
    writer = FFMpegWriter(fps=60, metadata=metadata)
    fig, ax = plt.subplots()

    with writer.saving(fig, output_file, 100):
        for frame, die_size in frames:  # 每一幀包含 cells 和 die_size
            ax.clear()
            draw_layout(ax, frame, die_size)
            writer.grab_frame()
    plt.close(fig)

def visualize_steps(layout_data, opt_steps, post_layout):
    frames = []
    current_cells = layout_data["cells"].copy()
    die_size = layout_data["die_size"]  # 提取 DieSize
    frames.append((current_cells, die_size))  # 添加初始佈局
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
        frames.append((current_cells.copy(), die_size))
    frames.append((current_cells.copy(), die_size))  # 添加最終佈局
    return frames

def draw_layout(ax, cells, die_size):
    """
    繪製佈局，根據 DieSize 設定 X 和 Y 軸的範圍
    """
    ax.set_xlim(die_size[0], die_size[2])  # DieSize 的 x 最小值和最大值
    ax.set_ylim(die_size[1], die_size[3])  # DieSize 的 y 最小值和最大值

    for cell in cells:
        rect = plt.Rectangle(
            (cell["x"], cell["y"]),
            cell["w"],
            cell["h"],
            edgecolor="black",
            facecolor="blue" if not cell["fixed"] else "red",
            alpha=0.7
        )
        ax.add_patch(rect)

# 主程式
def main():
    parser = argparse.ArgumentParser(description="Generate MP4 for layout optimization steps.")
    parser.add_argument("-lg", required=True, help="Input .lg file.")
    parser.add_argument("-opt", required=True, help="Input .opt file.")
    parser.add_argument("-postlg", required=True, help="Input .postlg file.")
    parser.add_argument("-o", required=True, help="Output MP4 file.")
    args = parser.parse_args()
    layout_data, opt_steps, post_layout = parse_files(args.lg, args.opt, args.postlg)
    frames = visualize_steps(layout_data, opt_steps, post_layout)
    generate_mp4(frames, args.o)

if __name__ == "__main__":
    main()
