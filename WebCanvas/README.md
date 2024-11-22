# 使用教學：Optimizer and Legalizer Process Visualization

## 動畫展示

<video width="800" height="600" controls>
  <source src="./video/testcase1_16900_20241122_165801.mp4" type="video/mp4">
  您的瀏覽器不支援 HTML5 視訊標籤，請下載檔案觀看：
  <a href="./video/testcase1_16900_20241122_165801.mp4">下載 MP4 檔案</a>
</video>

---

## 步驟 1：下載專案

1. 使用 `git clone` 指令將專案下載到本地：

   ```bash
   git clone https://github.com/coherent17/Optimizer-and-Legalizer-Co-optimization.git
   ```

2. 進入專案目錄：

   ```bash
   cd Optimizer-and-Legalizer-Co-optimization
   ```

3. 進入 `WebCanvas` 資料夾：
   ```bash
   cd WebCanvas
   ```

---

## 步驟 2：環境準備

1. **確認已安裝 Node.js 和 npm：**

   - 檢查 Node.js：
     ```bash
     node -v
     ```
     此指令會顯示 Node.js 的版本。
   - 檢查 npm：
     ```bash
     npm -v
     ```
     此指令會顯示 npm 的版本。

2. **確認已安裝 FFmpeg：**

   - 檢查 FFmpeg 是否已安裝：
     ```bash
     ffmpeg -version
     ```
     此指令會顯示 FFmpeg 的版本。若未安裝，請根據您的操作系統安裝 FFmpeg：
     - **Windows**：前往 [FFmpeg 官方網站](https://ffmpeg.org/) 下載並安裝。
     - **macOS**：使用 Homebrew 安裝：
       ```bash
       brew install ffmpeg
       ```
     - **Linux**：使用套件管理器安裝，例如：
       ```bash
       sudo apt install ffmpeg
       ```

   > 如果伺服器未安裝 FFmpeg，影片轉檔功能將無法正常運作。

---

## 步驟 3：安裝專案依賴

在 `WebCanvas` 資料夾中執行以下指令安裝所需的依賴：

```bash
npm install
```

---

## 步驟 4：啟動伺服器

1. 啟動伺服器：

   ```bash
   node server.js
   ```

2. 在瀏覽器中打開 [http://localhost:3000](http://localhost:3000) 即可訪問網頁。

---

## 步驟 5：上傳檔案並執行動畫

1. 在網頁界面上選擇並上傳以下檔案：

   - `.lg` 檔案，例如 `xxx.lg`
   - `.opt` 檔案，例如 `xxx.opt`
   - `_post.lg` 檔案，例如 `xxx_post.lg`

2. 按下 **Start Animation** 按鈕開始動畫與錄製：
   - **第一次按下**：啟動動畫並開始錄製 WebM 檔案。
   - **第二次按下**：暫停動畫並將錄製的 WebM 檔案轉換為 MP4 檔案。
   - **第三次按下**：繼續動畫並繼續錄製。

---

## 功能描述

- **動畫視覺化**：將 `.lg`, `.opt`, 和 `_post.lg` 檔案中的資料進行解析並動畫化。
- **錄製影片**：動畫過程將錄製為 WebM 格式，並在伺服器端自動轉換為 MP4 格式。
- **進度控制**：使用者可以通過按鈕控制動畫的開始、暫停與繼續。

---

## 注意事項

1. 確保您的環境已安裝 **Node.js**、**npm** 和 **FFmpeg**。
2. 確保上傳的檔案格式正確（`.lg`, `.opt`, `_post.lg`）。
3. 如果伺服器端未安裝 FFmpeg，請參考環境準備步驟進行安裝。

---

## 作者資訊

- **作者**：游竣量
- **學校**：國立清華大學 資訊工程研究所
- **學年**：研二
- **學號**：a131118

---
