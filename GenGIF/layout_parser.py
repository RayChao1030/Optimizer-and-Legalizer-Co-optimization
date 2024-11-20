def parse_files(lg_file, opt_file, postlg_file):
    layout_data = parse_lg(lg_file)
    opt_steps = parse_opt(opt_file)
    post_layout = parse_postlg(postlg_file)
    return layout_data, opt_steps, post_layout

def parse_lg(lg_file):
    with open(lg_file, "r") as f:
        lines = f.readlines()
    # Parse .lg file into structured data
    layout = {
        "die_size": [],
        "cells": [],
        "rows": []
    }
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

    positions = []  # 用於儲存 merged FF 的位置
    moved_cells = []  # 用於儲存移動的單元資訊

    i = 0
    while i < len(lines):
        # 解析 merged FF 的位置
        merged_ff = list(map(int, lines[i].split()))  # <merged ff x> <merged ff y>
        positions.append({"x": merged_ff[0], "y": merged_ff[1]})
        i += 1

        # 解析 num of moved cell
        num_of_cells = int(lines[i].strip())  # <num of moved cell>
        i += 1

        # 若 num_of_cells > 0，解析移動單元資訊
        if num_of_cells > 0:
            for _ in range(num_of_cells):
                cell_info = lines[i].split()  # <cell_name> <cell_x> <cell_y>
                moved_cells.append({
                    "name": cell_info[0],
                    "x": int(cell_info[1]),
                    "y": int(cell_info[2])
                })
                i += 1
        # 如果 num_of_cells 為 0，直接跳到下一個區塊

    return positions, moved_cells

