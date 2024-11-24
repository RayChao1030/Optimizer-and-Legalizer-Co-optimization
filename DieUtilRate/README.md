# **Placement Row Grid Usage and Visualization (GIF)**

📊 視覺化 **MBFF** 優化過程中的 **面積使用率變化**，並產生 GIF 動畫，展示每次優化後的格狀區域 (grid) 使用率！

---

## 📝 **簡介**
本專案主要功能是模擬並視覺化在多次優化過程中，placement row grid 的面積使用率變化。程式會：
1. 解析輸入檔案 (`*.lg`, `*.opt`, `*_post.lg`)。
2. 計算每次操作後的 placement row region 使用率。
3. 將所有圖片匯總為 `.gif`，呈現面積使用率變化過程。

---

## 📂 **目錄結構**

```plaintext
.
├── README.md
├── UTIL_RATE.py
├── myenv
├── tc
├── testcase1_16900.gif
├── testcase1_ALL0_5000.gif
├── testcase1_MBFF_LIB_7000.gif
└── testcase2_100.gif
```

## 🚀 快速開始

1. 安裝必要套件 matplotlib  

2. 將測試檔案 (`*.lg`, `*.opt`, `*_post.lg`) 放入 `./tc` 資料夾。

3. 執行程式，使用以下指令執行程式，生成面積使用率 GIF 動畫：

範例指令：
```plaintext
python UTIL_RATE.py <lgFile> <optFile> <postLgFile> <xStepNum> <yStepNum> <stepCut>
```
指令說明：

	•	<lgFile>: .lg 檔案路徑。
	•	<optFile>: .opt 檔案路徑。
	•	<postLgFile>: _post.lg 檔案路徑。
	•	<xStepNum>: X 軸格數。
	•	<yStepNum>: Y 軸格數。
	•	<stepCut>: 每隔幾步生成圖檔。

實際範例：
```plaintext
python UTIL_RATE.py ./tc/testcase1_ALL0_5000.lg ./tc/testcase1_ALL0_5000.opt ./tc/testcase1_ALL0_5000_post.lg 16 16 100
python UTIL_RATE.py ./tc/testcase1_16900.lg ./tc/testcase1_16900.opt ./tc/testcase1_16900_post.lg 10 10 50
python UTIL_RATE.py ./tc/testcase1_MBFF_LIB_7000.lg ./tc/testcase1_MBFF_LIB_7000.opt ./tc/testcase1_MBFF_LIB_7000_post.lg 20 20 400
python UTIL_RATE.py ./tc/testcase2_100.lg ./tc/testcase2_100.opt ./tc/testcase2_100_post.lg 20 20 100
```
4. 輸出結果

執行完成後，輸出使用率變化的動畫 GIF，存放於本資料夾

## 🖼️ 圖例說明

	•	XY 軸: 將 placement row region 切分為 <xStepNum> * <yStepNum> 個格狀區域 (grid)。
	•	顏色深淺: 表示每個格子的 面積使用率 (白色：低使用率，紅色：高使用率)。

## 🛠️ 環境測試
	•	已測試: macOS


## 🎥 Enjoy visualizing your MBFF optimization process!
### testcase1_16900
![testcase1_16900](./testcase1_16900.gif)
### testcase1_ALL0_5000
![testcase1_ALL0_5000](./testcase1_ALL0_5000.gif)
### testcase2_100
![testcase2_100](./testcase2_100.gif)
### testcase1_MBFF_LIB_7000
![testcase1_MBFF_LIB_7000](./testcase1_MBFF_LIB_7000.gif)