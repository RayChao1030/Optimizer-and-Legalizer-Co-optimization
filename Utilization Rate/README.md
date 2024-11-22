# Die Area Usage Simulation and Visualization

## 簡介
模擬和視覺化 MBFF 優化過程中 Die 面積使用率的變化，逐步模擬 Flip-Flop 的操作，並繪製使用率的折線圖。

---

## 功能說明
1. **解析 `.lg` 檔案**  
2. **解析 `.opt` 檔案**  
   - 分析 MBFF 的轉換步驟（source Flip-Flops 及 new Flip-Flop）。
3. **模擬步驟與計算面積使用率**  。
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

```

---

# 安裝與執行

## 1. 建立 Python 虛擬環境
在專案目錄下執行以下指令：

```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
pip install matplotlib    # 安裝必要套件
```

## 2. 準備測試檔案
將測試檔案放置於 ../testcases/ 資料夾下

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




