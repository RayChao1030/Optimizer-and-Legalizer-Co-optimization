# Die Area Usage Simulation and Visualization

## 簡介
模擬和視覺化 MBF（Multi-bit Flip-Flops, MBFF）優化過程中 Die 面積使用率的變化。透過分析 `.lg` 和 `.opt` 檔案，逐步模擬 Flip-Flop 的操作，並繪製使用率的折線圖，了解面積的變化情況。

---

## 功能說明
1. **讀取與解析 `.lg` 檔案**  
   - 提取 Die 參數（如 Alpha、Beta、DieSize）。
   - 紀錄所有的 Flip-Flop 資料（位置、大小等）。
2. **讀取與解析 `.opt` 檔案**  
   - 分析 MBFF 的轉換步驟（來源 Flip-Flops 及新增 Flip-Flop）。
3. **模擬步驟與計算面積使用率**  
   - 根據 `.opt` 檔案模擬每一步操作。
   - 計算每個步驟後的 Die 面積使用率。
4. **視覺化面積使用率**  
   - 繪製折線圖並輸出為 `.png` 圖檔。

---

## 目錄結構
```plaintext
.
├── draw_utilization_rate.py          # 主程式
├── testcase1_16900_die_usage_rate_plot.png
├── testcase1_ALL0_5000_die_usage_rate_plot.png
├── testcase1_MBFF_LIB_7000_die_usage_rate_plot.png
├── testcase2_100_die_usage_rate_plot.png
├── testcase3_4579_die_usage_rate_plot.png
├── venv                              # Python 虛擬環境
└── testcases/                        # 測試資料目錄 (請自備)

---

# 安裝與執行

## 1. 建立 Python 虛擬環境
在專案目錄下執行以下指令：

```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
pip install matplotlib    # 安裝必要套件

## 2. 準備測試檔案
將測試檔案放置於 testcases/ 資料夾下。測試檔案命名格式如下：

<測試檔案名稱>.lg
<測試檔案名稱>.opt
testcases/testcase1_16900.lg
testcases/testcase1_16900.opt

## 3. 執行程式
python draw_utilization_rate.py

## 4. 輸出結果
testcase1_16900_die_usage_rate_plot.png

## 5. 圖例
- X 軸：步驟
- Y 軸：面積使用率 (%)




