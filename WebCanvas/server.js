// server.js
const express = require("express");
const path = require("path");
const multer = require("multer");
const { exec } = require("child_process");
const fs = require("fs");

const app = express();
const PORT = 3000;

// Define the directory for storing video files using a relative path
const videoDir = "./video";

app.use(express.static(path.join(__dirname, "public")));

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, videoDir);
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 1 * 1024 * 1024 * 1024 }, // Set the file size limit to 1GB
});

app.use(express.json({ limit: "1gb" }));
app.use(express.urlencoded({ limit: "1gb", extended: true }));

// Function to check if FFmpeg is installed and accessible
function checkFFmpeg(callback) {
  exec("ffmpeg -version", (error, stdout) => {
    if (error) {
      console.error("FFmpeg is not installed or not in PATH.");
      return callback(false);
    }
    console.log("FFmpeg is installed.");
    return callback(true);
  });
}

// Handle POST requests to upload video files
app.post("/upload", upload.single("video"), (req, res) => {
  const prefix = req.body.prefix;
  if (!prefix) {
    return res.status(400).send("File prefix is missing.");
  }

  console.log(`Received prefix: ${prefix}`);

  const inputPath = path.join(videoDir, `${prefix}.webm`);
  const outputPath = path.join(videoDir, `${prefix}.mp4`);

  // Check if the input file exists
  if (!fs.existsSync(inputPath)) {
    return res.status(400).send(`Input file not found: ${inputPath}`);
  }

  // Check if FFmpeg is installed
  checkFFmpeg((isInstalled) => {
    if (!isInstalled) {
      return res.status(500).send("FFmpeg is not installed on the server.");
    }

    console.log("Starting video conversion...");

    // Construct the FFmpeg command for video conversion
    const command = `ffmpeg -y -i ${inputPath} -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -r 30 ${outputPath}`;
    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`FFmpeg encountered an error:\n${stderr}`);
        return res
          .status(500)
          .send(`Conversion failed due to an error: ${stderr}`);
      }

      if (stderr) {
        console.log(`FFmpeg process log:\n${stderr}`);
      }

      console.log("FFmpeg conversion completed successfully.");
      res.status(200).send(`Conversion successful. Output file: ${outputPath}`);
    });
  });
});

// Start the server and listen on the defined port
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
