import os
import sys
import matplotlib.pyplot as plt


def read_lg_file(filename):
    if not os.path.exists(filename):
        print(f"檔案 {filename} 不存在")
        return None

    data = {
        "parameters": {},  # 儲存 Alpha, Beta, DieSize 
        "flip_flops": []   # 儲存 FF 
    }

    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):  # 跳過空行和註解
                    continue
                
                parts = line.split()
                
                # parsing
                if parts[0] in ["Alpha", "Beta"]:
                    data["parameters"][parts[0]] = float(parts[1])
                elif parts[0] == "DieSize":
                    data["parameters"]["DieSize"] = list(map(int, parts[1:]))
                # parsing Flip-Flop
                elif parts[0].startswith("FF_"):
                    ff_data = {
                        "name": parts[0],
                        "x": int(parts[1]),
                        "y": int(parts[2]),
                        "width": int(parts[3]),
                        "height": int(parts[4]),
                        "fix_status": parts[5]
                    }
                    data["flip_flops"].append(ff_data)
    except Exception as e:
        print(f"讀檔錯誤: {e}")
        return None

    return data


def read_opt_file(filename):
    if not os.path.exists(filename):
        print(f"檔案 {filename} 不存在")
        return None

    banking_cells = []

    try:
        with open(filename, "r") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):  # 跳過空行和註解
                    continue
                
                # 判斷是否為 Banking_Cell 
                if line.startswith("Banking_Cell:"):
                    parts = line.split()
                    ff_list = parts[1:parts.index("-->")]
                    new_ff = parts[parts.index("-->") + 1]
                    x, y, w, h = map(int, parts[-4:])
                    banking_cell = {
                        "source_ffs": ff_list,
                        "new_ff": {
                            "name": new_ff,
                            "width": w,
                            "height": h
                        }
                    }
                    banking_cells.append(banking_cell)
    except Exception as e:
        print(f"讀檔錯誤: {e}")
        return None

    return banking_cells


def calculate_die_area(die_size):
    """計算 Die 的面積"""
    x1, y1, x2, y2 = die_size
    return (x2 - x1) * (y2 - y1)


def calculate_area_usage(flip_flops, die_area):
    """計算面積使用率，percentage"""
    area_sum = sum(ff["width"] * ff["height"] for ff in flip_flops)
    usage_rate = (area_sum / die_area) * 100  # 轉為百分比
    return usage_rate


def simulate_steps(ff_result, opt_result, die_size):
    """模擬步驟並計算每隔一個步驟的面積使用率"""
    die_area = calculate_die_area(die_size)  # 計算 die 面積
    area_usage = {}  # 儲存每 step 的面積使用率
    current_ff_result = ff_result[:]  # init Flip-Flop 結果

    # Step -1：尚未進行任何操作的面積使用率
    area_usage[-1] = calculate_area_usage(current_ff_result, die_area)

    for index, step in enumerate(opt_result):
        # 更新
        sys.stdout.write(f"\r正在模擬步驟 {index}/{len(opt_result)}...")
        sys.stdout.flush()

        # 移除 source_ffs
        source_ffs = set(step["source_ffs"])
        current_ff_result = [ff for ff in current_ff_result if ff["name"] not in source_ffs]

        # 加入新的 new_ff
        current_ff_result.append(step["new_ff"])

        # 記錄該 step 的面積使用率
        area_usage[index] = calculate_area_usage(current_ff_result, die_area)

    # 換行
    sys.stdout.write("\n")
    return area_usage


if __name__ == "__main__":
    # 確定的檔案名稱列表
    testcases = [
        "../testcase/testcase1_16900",
        "../testcase/testcase1_ALL0_5000",
        "../testcase/testcase1_MBFF_LIB_7000",
        "../testcase/testcase2_100",
        "../testcase/testcase3_4579"
    ]

    for testcase in testcases:
        lg_filename = f"{testcase}.lg"
        opt_filename = f"{testcase}.opt"

        base_name = os.path.basename(testcase)
        output_filename = f"{base_name}_die_usage_rate_plot.png"
        #output_filename = f"{testcase}_die_usage_rate_plot.png"

        print(f"正在處理測試檔案: {testcase}")

        # 讀取 .lg 檔案
        lg_result = read_lg_file(lg_filename)
        if lg_result:
            print("LG 檔案內容成功讀取！")
            die_size = lg_result["parameters"]["DieSize"]
            print(f"Die 面積大小: {calculate_die_area(die_size)}")
            print(f"Flip-Flop 資料：共 {len(lg_result['flip_flops'])} 筆")

        # 讀取 .opt 檔案
        opt_result = read_opt_file(opt_filename)
        if opt_result:
            print("OPT 檔案內容成功讀取！")
            print(f"Banking_Cell 資料：共 {len(opt_result)} 筆")

        # 模擬步驟並計算面積使用率
        if lg_result and opt_result:
            area_usage = simulate_steps(lg_result["flip_flops"], opt_result, die_size)
            print(f"模擬完成，共計算 {len(area_usage)} 個步驟的面積使用率")

            # 顯示前 5 步和最後 5 步
            sorted_usage = sorted(area_usage.items())
            first_five = sorted_usage[:5]
            last_five = sorted_usage[-5:]

            print("面積使用率 - 前 5 步：")
            for step, usage in first_five:
                print(f"  Step {step}: {usage:.8f}%")

            print("面積使用率 - 後 5 步：")
            for step, usage in last_five:
                print(f"  Step {step}: {usage:.8f}%")

            # 比較 Step -1 和 Step last
            step_minus_one_usage = area_usage[-1]
            step_last_usage = area_usage[sorted_usage[-1][0]]
            usage_difference = step_last_usage - step_minus_one_usage
            print(f"Step -1 與 Step last 的面積使用率差異：{usage_difference:.8f}%")

            # 折線圖
            if area_usage:
                steps = list(area_usage.keys())  # 步驟
                usage_rates = list(area_usage.values())  # 面積使用率

                plt.figure(figsize=(12, 6))
                plt.plot(steps, usage_rates, marker='o', markersize=2, linewidth=1, label="Die Usage Rate (%)")
                plt.title(f"Die Area Usage Over Steps - {testcase}", fontsize=16)
                plt.xlabel("Steps", fontsize=14)
                plt.ylabel("Die Usage Rate (%)", fontsize=14)
                plt.grid(True, linestyle="--", alpha=0.7)
                plt.legend(fontsize=12)
                plt.tight_layout()

                # 存檔
                plt.savefig(output_filename)
                print(f"圖形已保存至檔案: {output_filename}")
                plt.close()  # 關閉

        print("-" * 50)  # 分隔線
