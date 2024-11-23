# Placement Row Grid Usage and Visualization

## 簡介
視覺化 MBFF 優化過程中面積使用率的變化
每隔一定次數的 opt 操作後，輸出一張 grid 面積使用率

---

## 功能說明
1. **解析 `.lg` `.opt` `_post.lg` 檔案**  
3. **模擬步驟與計算面積使用率**  。
   - 計算每個步驟後的 placement row grid 面積使用率(因為只有 placement row region 可以放置)
4. **視覺化面積使用率**  
   - 繪製使用率 `.png` 圖檔，並產生 .gif 檔案

---

## 目錄結構
```plaintext
├── 100
├── 16900
├── 5000
├── 7000
├── README.md
├── UTIL_RATE.py
├── tc

```

---

# 安裝與執行

## 1. 建立 Python 虛擬環境
在專案目錄下執行以下指令：

```bash
source myenv/bin/activate  # Linux/MacOS
myenv\Scripts\activate     # Windows
pip install matplotlib    # 安裝必要套件
```

## 2. 準備測試檔案
將測試檔案 `*.lg`, `*.opt`, `_post.lg` 放置於 ./tc/ 資料夾下即可

## 3. 執行程式
```bash
python UTIL_RATE.py *.lg *.opt *_post.lg <output_dir> <xStepNum> <yStepNum> <stepCut>
python UTIL_RATE.py *.lg *.opt *_post.lg ./output 10 20 1000
# Util Rate 圖片存放於 ./output, x 軸切為 10 等分, y 軸切為 20 等分，每 1000次 opt 繪製圖片與gif
#
python UTIL_RATE.py ./tc/testcase1_ALL0_5000.lg ./tc/testcase1_ALL0_5000.opt ./tc/testcase1_ALL0_5000_post.lg ./5000 16 16 100 # 約執行 25 秒
python UTIL_RATE.py ./tc/testcase1_16900.lg ./tc/testcase1_16900.opt ./tc/testcase1_16900_post.lg ./16900 10 10 50 # 約執行 25 秒
python UTIL_RATE.py ./tc/testcase1_MBFF_LIB_7000.lg ./tc/testcase1_MBFF_LIB_7000.opt ./tc/testcase1_MBFF_LIB_7000_post.lg ./7000 20 20 400 # 約執行 35 秒
python UTIL_RATE.py ./tc/testcase2_100.lg ./tc/testcase2_100.opt ./tc/testcase2_100_post.lg ./100 20 20 100 # 約執行 25 秒
```

## 4. 輸出結果
在目錄 output_dir 底下，輸出圖片與 gif
```bash
*_{流水號}.png # *為流水號，從 0 開始，每 1000次 baking 輸出一張圖
./output_dir/output.gif # 動畫 gif 顯示 util rate 變化
```

## 5. 圖例
- XY 軸：將 placement row region 切為 xStepNum * yStepNum 個 grid
- 深淺： 面積使用率

## 6. 其他
每隔 stepCut 次 opt opration 後，根據 *.opt, *_post.lg , 畫出當前 placement region 使用率

mac 環境下實作測試，windows 尚未測試


