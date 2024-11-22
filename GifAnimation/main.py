import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
import numpy as np
from tqdm import tqdm
import imageio
import argparse

def parse_lg_file(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()
    die_size = None
    blocks = []
    rows = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"): continue
        fields = line.split()
        if line.startswith("DieSize") and len(fields) == 5:
            _, x1, y1, x2, y2 = fields
            die_size = (int(x1), int(y1), int(x2), int(y2))
        elif line.startswith("PlacementRows") and len(fields) == 6:
            _, startX, startY, siteWidth, siteHeight, totalNumOfSites = fields
            rows.append((int(startX), int(startY), int(siteWidth), int(siteHeight), int(totalNumOfSites)))
        elif len(fields) == 6 and fields[5] in ["FIX", "NOTFIX"]:
            name, x, y, width, height, fix_status = fields
            blocks.append((name, int(x), int(y), int(width), int(height), fix_status))
    return die_size, blocks, rows

def parse_opt_file(file_path):
    steps = []
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith("Banking_Cell:"):
                parts = line.strip().split("-->")
                ff_list = parts[0].replace("Banking_Cell:", "").strip().split()
                merged_info = parts[1].strip().split()
                steps.append({
                    'to_remove': ff_list,
                    'new_cell': {
                        'name': merged_info[0],
                        'x': int(merged_info[1]),
                        'y': int(merged_info[2]),
                        'width': int(merged_info[3]),
                        'height': int(merged_info[4])
                    }
                })
    return steps

def parse_post_file(file_path):
    results = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            fields = line.split()
            if len(fields) >= 2:
                results.append({
                    'merged_position': (int(fields[0]), int(fields[1])),
                    'moved_cells': []
                })
    return results

def draw_static_elements(ax, rows, die_size):
    row_patches = []
    for row in rows:
        startX, startY, siteWidth, siteHeight, totalNumOfSites = row
        rect = patches.Rectangle(
            (startX, startY), siteWidth * totalNumOfSites, siteHeight,
            linewidth=0.5, edgecolor="lightgray", linestyle="dotted",
            facecolor="none", antialiased=True
        )
        row_patches.append(rect)
    collection = PatchCollection(row_patches, match_original=True)
    ax.add_collection(collection)


def create_animation(die_size, initial_blocks, rows, opt_steps, post_results, output_path='layout_optimization.gif'):
    plt.style.use('fast')
    
    # 減小圖片尺寸
    fig, ax = plt.subplots(figsize=(16, 12), dpi=80)
    plt.subplots_adjust(top=0.95, bottom=0.05, left=0.05, right=0.85)
    
    print("Generating layout animation:")
    
    frames = []
    total_steps = len(opt_steps)
    
    num_samples = 30
    sample_interval = max(1, total_steps // num_samples)
    sample_steps = list(range(0, total_steps, sample_interval))
    if total_steps not in sample_steps:
        sample_steps.append(total_steps)
    
    margin = 0.05
    x_range = die_size[2] - die_size[0]
    y_range = die_size[3] - die_size[1]
    x_margin = x_range * margin
    y_margin = y_range * margin
    
    legend_elements = [
        patches.Patch(facecolor="#FF4444", label="FIX"),
        patches.Patch(facecolor="#4444FF", label="NOTFIX"),
        patches.Patch(facecolor="#44FF44", label="MERGED")
    ]
    
    def set_plot_limits():
        ax.set_xlim(die_size[0] - x_margin, die_size[2] + x_margin)
        ax.set_ylim(die_size[1] - y_margin, die_size[3] + y_margin)
        ax.set_aspect('equal', adjustable='box')
    
    # 創建臨時文件夾存放幀
    import tempfile
    import os
    temp_dir = tempfile.mkdtemp()
    
    try:
        for i, step in enumerate(tqdm(sample_steps, desc="Generating frames")):
            ax.clear()
            set_plot_limits()
            draw_static_elements(ax, rows, die_size)
            
            current_blocks = initial_blocks.copy()
            
            blocks_to_remove = set()
            merged_blocks = []
            for step_idx in range(step):
                if step_idx < len(opt_steps):
                    blocks_to_remove.update(opt_steps[step_idx]['to_remove'])
                    new_cell = opt_steps[step_idx]['new_cell']
                    merged_pos = post_results[step_idx]['merged_position']
                    merged_blocks.append((
                        new_cell['name'],
                        merged_pos[0],
                        merged_pos[1],
                        new_cell['width'],
                        new_cell['height'],
                        'MERGED'
                    ))
            
            current_blocks = [b for b in current_blocks if b[0] not in blocks_to_remove] + merged_blocks
            
            patches_list = [
                patches.Rectangle(
                    (block[1], block[2]), block[3], block[4],
                    color="#FF4444" if block[5] == "FIX" else "#4444FF" if block[5] == "NOTFIX" else "#44FF44",
                    alpha=0.8
                )
                for block in current_blocks
            ]
            
            collection = PatchCollection(patches_list, match_original=True)
            ax.add_collection(collection)
            
            ax.legend(handles=legend_elements, 
                     loc='center left', 
                     bbox_to_anchor=(1.02, 0.5),
                     fontsize=16)
            
            progress = (step / total_steps) * 100
            if step == total_steps:
                title = "Final Layout (100%)"
            else:
                title = f"Layout Progress: {progress:.1f}% (Step {step}/{total_steps})"
            ax.set_title(title, fontsize=20, pad=20)
            
            # 保存為臨時文件
            temp_file = os.path.join(temp_dir, f'frame_{i:03d}.png')
            plt.savefig(temp_file, bbox_inches='tight', pad_inches=0.1)
            frames.append(imageio.imread(temp_file))
            
            if step == total_steps:
                for _ in range(5):
                    frames.append(frames[-1])
        
        plt.close()
        
        print(f"\nSaving animation to {output_path}...")
        imageio.mimsave(output_path, frames, fps=5, loop=0)
        print("Animation saved successfully!")
        
    finally:
        # 清理臨時文件
        import shutil
        shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description='Layout Optimization Animation Generator')
    
    parser.add_argument('--lg', type=str, required=True,
                        help='Input .lg file path')
    parser.add_argument('--opt', type=str, required=True,
                        help='Input .opt file path')
    parser.add_argument('--post', type=str, required=True,
                        help='Input post file path')
    parser.add_argument('--output', type=str, default='layout_optimization.gif',
                        help='Output GIF file path (default: layout_optimization.gif)')
    
    args = parser.parse_args()
    
    try:
        print(f"Reading files...")
        die_size, blocks, rows = parse_lg_file(args.lg)
        opt_steps = parse_opt_file(args.opt)
        post_results = parse_post_file(args.post)
        
        create_animation(die_size, blocks, rows, opt_steps, post_results, output_path=args.output)
        
    except FileNotFoundError as e:
        print(f"Error: Could not find file - {e.filename}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()