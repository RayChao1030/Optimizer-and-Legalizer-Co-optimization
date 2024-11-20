import matplotlib.pyplot as plt
from PIL import Image
def generate_animation(frames, output_file):
    """
    Generate a GIF/MP4 from a list of PIL Image frames.
    """
    frames[0].save(
        output_file,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=500  # 每幀持續時間（毫秒）
    )

def visualize_steps(layout_data, opt_steps, post_layout):
    frames = []
    current_cells = layout_data["cells"].copy()  # 目前的單元集合

    # 初始佈局
    frames.append(draw_layout(layout_data, current_cells))

    # 逐步處理 opt_steps
    for step in opt_steps:
        # 移除被合併的單元
        current_cells = [cell for cell in current_cells if cell["name"] not in step["inputs"]]

        # 添加新合併單元
        current_cells.append({
            "name": step["output"],
            "x": step["x"],
            "y": step["y"],
            "w": step["w"],
            "h": step["h"],
            "fixed": False  # 新單元默認為非固定
        })

        # 繪製當前狀態
        frames.append(draw_layout(layout_data, current_cells))

    # 最終佈局
    frames.append(draw_layout(layout_data, current_cells, final=True))
    return frames


def draw_layout(layout_data, cells, final=False):
    fig, ax = plt.subplots()
    die_size = layout_data["die_size"]

    # 設置佈局範圍
    ax.set_xlim(die_size[0], die_size[2])
    ax.set_ylim(die_size[1], die_size[3])

    # 繪製所有單元
    for cell in cells:
        draw_cell(ax, cell, color="blue" if not cell["fixed"] else "red")

    # 繪製最終佈局標記
    if final:
        ax.set_title("Final Layout")
    else:
        ax.set_title("Intermediate Layout")

    # 保存當前圖像
    fig.canvas.draw()
    image = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
    plt.close(fig)
    return image

def draw_cell(ax, cell, color="blue"):
    """
    在圖上繪製一個矩形，表示佈局中的單元。
    """
    rect = plt.Rectangle(
        (cell["x"], cell["y"]),  # 左下角座標
        cell["w"], cell["h"],   # 寬度和高度
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
