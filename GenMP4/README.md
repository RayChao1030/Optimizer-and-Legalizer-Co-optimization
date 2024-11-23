# Fast Optimization Visualizer

## demo
- **Normal Mode**

[Video Placeholder]

- **Detail Mode**  (fps set to 2 for better visual effect)

[Video Placeholder]

## Requirements
- **Platform**: Tested on Windows. Other platforms have not been tested, but the program requires a screen to run.
- The environment can be set up using the `environment.yml` file.

## Usage
To run the visualizer, use the following command:
```bash
$ main.py -lg *.lg -opt *.opt -postlg *_post.lg -o output.mp4 [-display] [-detail] [-vcodec VCODEC] [-preset PRESET] [-crf CRF] [-pix_fmt PIX_FMT] [-framerate FPS]
```

## Arguments
- Input Files:
  - `-lg`: Initial cell file
  - `-opt`: Optimization step file
  - `-postlg`: Legalizer output file
- Output File:
  - `-o`: Specifies the video output file. Supports all formats compatible with `ffmpeg`.
- Options
  - `-display`: Enables rendering frames on the screen. Rendering is faster without display.
  - `-detail`: Enables detailed mode, in each step, it will place merge cell first, and then move all overlapped cell one by one in each frame
- FFmpeg Settings:
  - argument pass to ffmpeg, see [ffmpeg documentation](https://www.ffmpeg.org/ffmpeg.html) for more information
  - `-vcodec`: Video codec (default: `h264`)
  - `-preset`: Encoding speed/quality trade-off (default: `ultrafast`)
  - `-crf`: Quality factor (default: `18`)
  - `-pix_fmt`: Pixel format (default: `yuv444p`)
  - `-framerate`: Video frame rate (default: `60`)

## Generating a GIF
- To convert the MP4 output to a GIF, use the following `ffmpeg` command (included in the environment):
```bash
$ ffmpeg -ss 30 -t 3 -i input.mp4 \
    -vf "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
    -loop 0 output.gif
```
-  Detailed instructions are available in this [Stack Exchange post](https://superuser.com/questions/556029/how-do-i-convert-a-video-to-gif-using-ffmpeg-with-reasonable-quality)

## Color Guide

1. **Gray**: Not fixed cells
2. **Dark Gray**: Fixed cells
3. **Blue**: Merged cells
4. **Cyan (Filled)**: Merged cell in current step
5. **Red**: Cells needing legalization
6. **Green**: Cells legalized in this step
- You can change all above color in the header part of `main.py`

## Results
### Runtime Performance (very fast!)
  - All data below is generated using the settings: `-crf 18 -vcodec h264 -preset ultrafast`

|      Testcase     |# of Steps|# of Moved Cells|Output time|Runtime|Generate Speed|
|-------------------|----------|----------------|-----------|-------|--------------|
|  testcase1_16900  |    1781  |      1438      |    29s    | 11.81s|   150.80fps  |
|testcase1_ALL0_5000|    3420  |      8420      |    57s    | 21.70s|   157.60fps  |
|   testcase2_100   |    2949  |      654       |    49s    | 23.63s|   124.79fps  |
|testcase1_MBFF_LIB_7000|9632  |      9396      |    160s   | 61.77s|   155.93fps  |

- Videos of large test cases are omitted due to size constraints, only the small test cases (`testcase1_16900`, `testcase2`) are shown at the beginning of this readme. For other test cases, refer to the MP4 files in the folder.

### Performance Comparison: Encoding Settings

| h264 |    preset   | veryslow |  slow | medium | fast |veryfast|ultrafast|
|------|-------------|----------|-------|--------|------|--------|---------|
|crf=0 | runtime(s)  |  17.17   | 14.82 |  15.14 | 13.67|  13.46 |  12.38  |
|      |file size(KB)|  12646   | 12717 |  12947 | 12941|  13329 |  23141  |
|crf=18| runtime(s)  |  28.68   | 21.08 |  16.91 | 13.6 |  14.02 | *12.36* |
|      |file size(KB)|  12810   | 13289 |  13177 | 12762|  10552 |  22972  |
|crf=23| runtime(s)  |  29.92   | 18.92 |  15.4  | 13.99|  13.06 |  12.38  |
|      |file size(KB)|  10551   | 10780 |  10689 | 10389|   8453 |  18263  |

| h265 |    preset   | veryslow |  slow | medium | fast |veryfast|ultrafast|
|------|-------------|----------|-------|--------|------|--------|---------|
|crf=0 | runtime(s)  |  279.19  | 29.95 |  17.18 | 17.07|  16.16 |   15    |
|      |file size(KB)|  23334   | 22971 |  23585 | 23585|  22539 |  27940  |
|crf=18| runtime(s)  |  234.04  | 28.14 |  16.9  | 17.11|  16.24 |  14.54  |
|      |file size(KB)|  12476   | 12476 |  12222 | 11493|  11510 |  13487  |
|crf=23| runtime(s)  |  207.54  | 27.84 |  16.82 | 16.75|  15.98 |  14.66  |
|      |file size(KB)|   9951   | 9615  |   9469 | 8762 |   8733 |  10091  |
|crf=28| runtime(s)  |  187.16  | 28.97 |  16.58 | 15.65|  15.65 |  14.56  |
|      |file size(KB)|   7417   | 7086  |   6815 | 6143 | *6071* |   6975  |
- **Observations**
  - HEVC provides better quality and smaller file sizes compared to H.264.
  - H.264 has faster encoding times.
  - crf 23 in H.264 is approximately same as crf 28 in HEVC
  - H.264 is generally greater than HEVC on runtime
  - HEVC is generally greater than H.264 on file size
- **Recommended settings:**
  - Best Runtime: `h264`, `ultrafast`
  - Smallest File Size: `hevc`, `veryfast`

