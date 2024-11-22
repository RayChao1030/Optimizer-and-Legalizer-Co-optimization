// script.js
// DOM Elements
const lgInput = document.getElementById("lgFile");
const optInput = document.getElementById("optFile");
const postLgInput = document.getElementById("postLgFile");
const startButton = document.getElementById("startButton");
const progressDiv = document.getElementById("progress");

// Recording States
const NOT_RECORDING = 0;
const RECORDING = 1;
const PAUSED = 2;

// Constants
const FPS = 30;
const ANIMATION_SCALE_FACTOR = 0.1;
const ANIMATION_FRAMES = 30;

// Global Variables
let mediaRecorder;
let recordedChunks = [];
let lgData = null;
let bankingCells = null;
let canvas, ctx;
let scaleX, scaleY;
let animationProgress = 0;
let currentBankingIndex = 0;
let cellsByName = {};
let movingCells = {};
let pendingMergedCell = null;
let videoPrefix = "";
let isRecording = NOT_RECORDING;
let isAnimationRunning = false;
let animationHandle = null;

// Event Listeners
lgInput.addEventListener("change", handleFileSelect);
optInput.addEventListener("change", handleFileSelect);
postLgInput.addEventListener("change", handleFileSelect);

function handleFileSelect() {
  if (lgInput.files[0]) {
    videoPrefix = lgInput.files[0].name.split(".")[0];
  }
  startButton.disabled = !(
    lgInput.files[0] &&
    optInput.files[0] &&
    postLgInput.files[0]
  );
}

function updateProgressMessage(message) {
  progressDiv.textContent = message;
}

function startRecording() {
  if (!canvas || !canvas.captureStream) {
    console.error("Canvas or captureStream not available.");
    return;
  }

  // Create a MediaStream from the canvas
  const stream = canvas.captureStream(FPS);
  const options = { mimeType: "video/webm; codecs=vp9" };
  recordedChunks = [];

  try {
    mediaRecorder = new MediaRecorder(stream, options);
  } catch (error) {
    console.error("Error creating MediaRecorder:", error);
    return;
  }

  // Collect video chunks
  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) recordedChunks.push(event.data);
  };

  mediaRecorder.start();
  console.log("Recording started");
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
    console.log("Recording stopped");

    // When recording stops, upload the video
    mediaRecorder.onstop = uploadRecording;
  } else {
    console.warn("Attempted to stop recording, but it was not active.");
  }
}

function uploadRecording() {
  if (!videoPrefix) {
    console.error("File prefix is not set.");
    return;
  }

  startButton.disabled = true;

  // Generate a timestamp in the format YYYYMMDD_HHMMSS
  const now = new Date();
  const timestamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(
    2,
    "0"
  )}${String(now.getDate()).padStart(2, "0")}_${String(now.getHours()).padStart(
    2,
    "0"
  )}${String(now.getMinutes()).padStart(2, "0")}${String(
    now.getSeconds()
  ).padStart(2, "0")}`;

  // Append the timestamp to the file name
  const fileName = `${videoPrefix}_${timestamp}.webm`;
  const fullPrefix = `${videoPrefix}_${timestamp}`;

  const blob = new Blob(recordedChunks, { type: "video/webm" });
  const formData = new FormData();
  formData.append("video", blob, fileName);
  formData.append("prefix", fullPrefix);

  // POST the video file to the server
  fetch("/upload", { method: "POST", body: formData })
    .then((response) => {
      if (response.ok) {
        updateProgressMessage("Recording uploaded and converted to MP4.");
      } else {
        return response.text().then((errorMessage) => {
          throw new Error(`Upload failed: ${errorMessage}`);
        });
      }
    })
    .catch((error) => {
      console.error("Error uploading video:", error);
      updateProgressMessage("Error uploading video. Please try again.");
    })
    .finally(() => {
      startButton.disabled = false;
    });
}

startButton.addEventListener("click", handleStartButtonClick);
function handleStartButtonClick() {
  if (isRecording === NOT_RECORDING) {
    updateProgressMessage("Reading files...");

    Promise.all([
      readFile(lgInput.files[0]),
      readFile(optInput.files[0]),
      readFile(postLgInput.files[0]),
    ])
      .then(([lgContent, optContent, postContent]) => {
        updateProgressMessage("Parsing files...");
        lgData = parseLgFile(lgContent);
        bankingCells = parseOptAndPostFiles(optContent, postContent);

        updateProgressMessage("Initializing animation...");
        initAnimation();

        // Start the recording and animation
        startRecording();
        isRecording = RECORDING;
        startButton.textContent = "Stop Recording";
        isAnimationRunning = true;
        updateProgressMessage("Recording and animation...");
        animate(); // Begin animation loop
      })
      .catch((error) => {
        console.error("Error reading files:", error);
        updateProgressMessage(
          "Error reading files. Please check the console for details."
        );
      });
  } else if (isRecording === RECORDING) {
    // If currently recording, pause the recording and animation
    stopRecording();
    isRecording = PAUSED;
    startButton.textContent = "Resume Recording";
    isAnimationRunning = false;
    updateProgressMessage("Animation paused.");
  } else if (isRecording === PAUSED) {
    // If paused, resume the recording and animation
    updateProgressMessage("Resuming animation...");
    startRecording();
    isRecording = RECORDING;
    startButton.textContent = "Stop Recording";
    isAnimationRunning = true;
    animate(); // Continue animation loop
  }
}

function readFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (evt) => resolve(evt.target.result);
    reader.onerror = (err) => reject(err);
    reader.readAsText(file);
  });
}

function parseLgFile(content) {
  try {
    const lines = content.split("\n");
    const data = {
      alpha: 0,
      beta: 0,
      dieSize: [0, 0, 0, 0],
      cells: [],
      fixedCells: [],
    };
    const cellRegex = /^(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(FIX|NOTFIX)$/;

    for (let line of lines) {
      line = line.trim();
      if (line.startsWith("Alpha")) {
        data.alpha = parseInt(line.split(" ")[1], 10);
      } else if (line.startsWith("Beta")) {
        data.beta = parseInt(line.split(" ")[1], 10);
      } else if (line.startsWith("DieSize")) {
        const parts = line.split(" ");
        data.dieSize = parts.slice(1).map(Number);
      } else if (cellRegex.test(line)) {
        const [, name, x, y, width, height, fixStatus] = line.match(cellRegex);
        const cell = {
          name,
          x: parseInt(x, 10),
          y: parseInt(y, 10),
          width: parseInt(width, 10),
          height: parseInt(height, 10),
          fixed: fixStatus === "FIX",
        };
        (cell.fixed ? data.fixedCells : data.cells).push(cell);
      }
    }
    return data;
  } catch (error) {
    console.error("Error parsing LG file:", error);
    throw new Error("Invalid LG file format.");
  }
}

function parseOptAndPostFiles(optContent, postContent) {
  try {
    const optLines = optContent.split("\n");
    const postLines = postContent.trim().split("\n");
    const bankingCells = [];
    const bankingCellRegex =
      /^Banking_Cell:\s+(.+)\s+-->\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$/;

    let postIndex = 0;
    for (let optLine of optLines) {
      optLine = optLine.trim();
      if (bankingCellRegex.test(optLine)) {
        const [, ffList, mergedName, x, y, w, h] =
          optLine.match(bankingCellRegex);
        const originalCells = ffList.trim().split(/\s+/);
        const [mergedX, mergedY] = postLines[postIndex++]
          .trim()
          .split(" ")
          .map(Number);
        const numMovedCells = parseInt(postLines[postIndex++].trim(), 10);
        const moveCells = {};
        for (let i = 0; i < numMovedCells; i++) {
          const [cellName, cellX, cellY] = postLines[postIndex++]
            .trim()
            .split(" ");
          moveCells[cellName] = {
            x: parseInt(cellX, 10),
            y: parseInt(cellY, 10),
          };
        }
        bankingCells.push({
          mergedName,
          x: mergedX,
          y: mergedY,
          width: parseInt(w, 10),
          height: parseInt(h, 10),
          originalCells,
          moveCells,
        });
      }
    }
    return bankingCells;
  } catch (error) {
    console.error("Error parsing Opt/Post files:", error);
    throw new Error("Invalid Opt/Post file format.");
  }
}

function initAnimation() {
  if (!canvas) {
    canvas = document.getElementById("canvas");
    ctx = canvas.getContext("2d");
  }

  const dieWidth = lgData.dieSize[2] - lgData.dieSize[0];
  const dieHeight = lgData.dieSize[3] - lgData.dieSize[1];
  scaleX = canvas.width / dieWidth;
  scaleY = canvas.height / dieHeight;

  cellsByName = {};
  lgData.cells.forEach(
    (cell) => (cellsByName[cell.name] = { ...cell, color: "lightgreen" })
  );
  lgData.fixedCells.forEach(
    (cell) => (cellsByName[cell.name] = { ...cell, color: "red" })
  );

  if (currentBankingIndex === 0) {
    setupCurrentBankingAnimation();
  }
}

function setupCurrentBankingAnimation() {
  if (currentBankingIndex >= bankingCells.length) {
    updateProgressMessage("Animation complete.");
    stopRecording();
    return;
  }

  const bankingCell = bankingCells[currentBankingIndex];
  pendingMergedCell = createMergedCell(bankingCell);
  movingCells = prepareMovingCells(bankingCell);

  animationProgress = 0;
}

function createMergedCell(bankingCell) {
  return {
    name: bankingCell.mergedName,
    x: bankingCell.x,
    y: bankingCell.y,
    width: bankingCell.width,
    height: bankingCell.height,
    color: "blue",
  };
}

function prepareMovingCells(bankingCell) {
  const cells = {};

  // Prepare original cells
  bankingCell.originalCells.forEach((name) => {
    const cell = cellsByName[name];
    if (cell) {
      cell.moving = true;
      cell.color = "blue";
      cells[name] = {
        cell,
        startX: cell.x,
        startY: cell.y,
        endX:
          pendingMergedCell.x +
          (cell.x - pendingMergedCell.x) * ANIMATION_SCALE_FACTOR,
        endY:
          pendingMergedCell.y +
          (cell.y - pendingMergedCell.y) * ANIMATION_SCALE_FACTOR,
      };
    }
  });

  // Prepare moved cells
  for (let [name, pos] of Object.entries(bankingCell.moveCells)) {
    const cell = cellsByName[name];
    if (cell) {
      cell.moving = true;
      cell.color = "orange";
      cells[name] = {
        cell,
        startX: cell.x,
        startY: cell.y,
        endX: pos.x + (cell.x - pos.x) * ANIMATION_SCALE_FACTOR,
        endY: pos.y + (cell.y - pos.y) * ANIMATION_SCALE_FACTOR,
      };
    }
  }

  return cells;
}

function finalizeAnimationStep() {
  Object.values(movingCells).forEach(({ cell, endX, endY }) => {
    cell.x = endX;
    cell.y = endY;
    cell.moving = false;
  });

  // Remove original cells and add the merged cell
  bankingCells[currentBankingIndex].originalCells.forEach(
    (name) => delete cellsByName[name]
  );
  cellsByName[pendingMergedCell.name] = pendingMergedCell;

  currentBankingIndex++;
  setupCurrentBankingAnimation();
}

function drawProgressText() {
  const step = currentBankingIndex + 1;
  const totalSteps = bankingCells.length;
  const mergeTarget = pendingMergedCell ? pendingMergedCell.name : "N/A";

  const progressText = `Step ${step} of ${totalSteps} - Merge Target: ${mergeTarget}`;

  ctx.fillStyle = "black";
  ctx.font = "16px Arial";
  ctx.textAlign = "right";

  ctx.fillText(progressText, canvas.width - 10, 20);
}

function animate() {
  if (!isAnimationRunning) {
    cancelAnimationFrame(animationHandle);
    return;
  }

  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw all cells
  for (let { x, y, width, height, color } of Object.values(cellsByName)) {
    ctx.fillStyle = color;
    ctx.fillRect(
      x * scaleX,
      canvas.height - (y + height) * scaleY,
      width * scaleX,
      height * scaleY
    );
  }

  // Update positions of moving cells
  animationProgress = Math.min(animationProgress + 10 / ANIMATION_FRAMES, 1);
  for (let { cell, startX, startY, endX, endY } of Object.values(movingCells)) {
    const t = animationProgress;
    cell.x = startX + (endX - startX) * t;
    cell.y = startY + (endY - startY) * t;
  }

  drawProgressText();

  // Complete animation step when progress reaches 100%
  if (animationProgress >= 1) {
    finalizeAnimationStep();
  }

  // Continue animation if there are more banking cells
  if (currentBankingIndex < bankingCells.length) {
    animationHandle = requestAnimationFrame(animate);
  } else {
    isAnimationRunning = false;
    document.getElementById("controls").style.display = "none";
  }
}
