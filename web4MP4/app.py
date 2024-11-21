from flask import Flask, render_template, send_from_directory, request, jsonify
import os

app = Flask(__name__)

# 指定影片文件夾
VIDEO_FOLDER = os.path.join(app.root_path, 'static')
app.config['VIDEO_FOLDER'] = VIDEO_FOLDER

# 假設 .lg 和 .opt 文件存放在與視頻相同的 static 資料夾下的子資料夾，例如 'data'
DATA_FOLDER = os.path.join(app.root_path, 'static', 'data')
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

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
    moved_cells_list = []
    i = 0
    while i < len(lines):
        # 解析合併單元格的位置
        merged_ff = list(map(int, lines[i].split()))
        positions.append({"x": merged_ff[0], "y": merged_ff[1]})
        i += 1
        if i >= len(lines):
            moved_cells_list.append([])
            break
        # 解析移動單元格的數量
        num_of_cells = int(lines[i].strip())
        i += 1
        current_moved_cells = []
        if num_of_cells > 0:
            for _ in range(num_of_cells):
                if i >= len(lines):
                    break
                cell_info = lines[i].split()
                current_moved_cells.append({
                    "name": cell_info[0],
                    "x": int(cell_info[1]),
                    "y": int(cell_info[2])
                })
                i += 1
        moved_cells_list.append(current_moved_cells)
    return positions, moved_cells_list

@app.route('/')
def index():
    # 列出 static 資料夾中的所有 MP4 文件
    video_files = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith('.mp4')]
    # 如果沒有 MP4 文件，預設為空列表
    if not video_files:
        video_files = []
    # 選擇預設播放的影片（第一個 MP4 文件）
    default_video = video_files[0] if video_files else None
    video_name = os.path.splitext(default_video)[0] if default_video else "No Video"
    return render_template('index.html', video_name=video_name, video_filename=default_video, video_list=video_files)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/get_step_detail', methods=['POST'])
def get_step_detail():
    print("Received /get_step_detail POST request")  # 調試用
    data = request.get_json()
    print(f"Request Data: {data}")  # 調試用

    video = data.get('video')
    step = data.get('step')

    if not video or not step:
        print("Missing 'video' or 'step' in request data")  # 調試用
        return jsonify({'status': 'error', 'message': 'Invalid parameters.'}), 400

    # 使用通用的 .opt 和 .lg 文件
    opt_filename = f"{video}.opt"
    postlg_filename = f"{video}_post.lg"

    opt_path = os.path.join(DATA_FOLDER, opt_filename)
    postlg_path = os.path.join(DATA_FOLDER, postlg_filename)

    print(f"Looking for files: {opt_path}, {postlg_path}")  # 調試用

    if not os.path.exists(opt_path) or not os.path.exists(postlg_path):
        print("One or both data files do not exist.")  # 調試用
        return jsonify({'status': 'error', 'message': 'Data not Provide!'}), 404

    try:
        steps = parse_opt(opt_path)
        positions, moved_cells_list = parse_postlg(postlg_path)

        num_steps_opt = len(steps)
        num_steps_lg = len(positions)

        # 確保請求的步驟在範圍內
        if step < 1 or step > num_steps_opt:
            print("Requested step is out of range in .opt file.")  # 調試用
            return jsonify({'status': 'error', 'message': 'Step out of range.'}), 404

        if step > num_steps_lg:
            print("Requested step is out of range in .lg file.")  # 調試用
            return jsonify({'status': 'error', 'message': 'Step out of range for position data.'}), 404

        step_index = step - 1
        step_data = steps[step_index]
        position = positions[step_index] if step_index < len(positions) else {'x': 0, 'y': 0}
        move_cell_list = moved_cells_list[step_index] if step_index < len(moved_cells_list) else []

        response = {
            'status': 'success',
            'merge_cell': step_data['output'],
            'merge_cell_position': {
                'x': step_data['x'],
                'y': step_data['y']
            },
            'delete_cell': step_data['inputs'],
            'number_of_move_cell': len(move_cell_list),
            'move_cell': move_cell_list
        }

        print(f"Response Data: {response}")  # 調試用
        return jsonify(response)

    except Exception as e:
        print(f"Error parsing files: {e}")  # 調試用
        return jsonify({'status': 'error', 'message': 'Error parsing data.'}), 500

@app.route('/debug_routes')
def debug_routes():
    """新增一個路由來列出所有已註冊的路由，以確認 /get_step_detail 是否存在"""
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        line = urllib.parse.unquote(f"{rule.endpoint}: {rule.rule} [{methods}]")
        output.append(line)
    return '<br>'.join(output)

if __name__ == '__main__':
    # 在 8080 端口啟動服務器
    app.run(host='0.0.0.0', port=8080, debug=True)