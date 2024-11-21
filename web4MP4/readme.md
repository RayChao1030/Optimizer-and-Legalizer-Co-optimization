# Web Optimize Step Visualization 

Web Optimize Step Visualization is a comprehensive web application designed to enhance PDA Lab3 video playback (Especially for GenMP4, 16ms per steps) 
by providing step-by-step visualization and detailed insights. This project integrates feature like speed control, case selection and steps detail searching.

## Table of Contents

- [Web Optimize Step Visualization](#web-optimize-step-visualization)
  - [Features & Demo](#features--demo)
  - [Technologies Used](#technologies-used)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Project Structure](#project-structure)
  - [API Integration](#api-integration)
  - [Customization](#customization)
  - [Acknowledgements](#acknowledgements)

## Features & Demo

![Optimize Step Visualization Demo](https://youtu.be/JjrR2taUtbU)

*Note: Replace the above placeholder with an actual screenshot or gif of the application in action.*

## Technologies Used

- **Frontend**:
  - HTML5
  - CSS3 (Bootstrap 4.5.2 for responsive design)
  - JavaScript (Vanilla JS for interactivity)
- **Backend**:
  - Flask (Assumed based on the use of `url_for` and Jinja templating)
- **Others**:
  - jQuery (Slim version for DOM manipulation)
  - Bootstrap Bundle for enhanced UI components

## Installation

To set up and run the Optimize Step Visualization application locally, make sure you have Flask==2.3.3.

### Steps

1. **Clone the Repository**

   git clone https://github.com/kevin/optimize-step-visualization.git
   cd optimize-step-visualization/web4MP4

2. **Put Data You want to Visualize**

   Put X.mp4 in the static directory. (X is the name)
    Put X_post.lg and X.opt in the static subdirectory data (/static/data/)

4. **Run the Application**

   python app.py
   The application should now be accessible at `http://127.0.0.1:8080/`.

## Usage

Once the application is running, follow these steps to utilize its features: (There also a demo video) 

1. **Select a Video**

   - Navigate to the top-right dropdown menu labeled "選擇影片" (Choose Video).
   - Select a video from the available list. If no videos are available, the dropdown will indicate as such.

2. **Control Playback Speed**

   - **Input Field**: Enter a desired speed value between `0.001x` and `10x` in the numeric input.
   - **Slider**: Use the range slider to adjust the speed dynamically.
   - **Preset Speed Buttons**: Click on buttons like `0.25x`, `0.5x`, `1x`, `2x`, or `4x` for quick speed adjustments.
   - The current playback speed is displayed below the controls.

3. **Navigate to a Specific Step**

   - Enter the desired step number in the "跳轉到哪一步" (Jump to Step) input field.
   - Click the `跳轉` (Jump) button to navigate to that step.
   - Alternatively, click the `跳轉＋查詢` (Jump + Query) button to jump to the step and fetch detailed information about it.

4. **View Current Step**

   - The "當前 Step" (Current Step) display updates in real-time as the video plays, indicating the current step number.

5. **Show Detailed Information**

   - Check the "Show Detail" checkbox to display detailed information about the current step.
   - Detailed data includes merged cells, their positions, deleted cells, and any moved cells.
   - Unchecking the box hides the details and resumes video playback.

## Project Structure

```
optimize-step-visualization/
├── static/
│   ├── videos/
│   │   ├── video1.mp4
│   │   ├── video2.mp4
│   │   └── ...
│   └── data/
│       └── video1.lg
│       └── video1.opt
│       └── ...
├── templates/
│   └── index.html
├── app.py
├── requirements.txt
└── README.md
```

- **static/**: Contains all static files like videos, CSS, and JavaScript.
  - **videos/**: Directory holding all video files available for playback.
  - **data/**: Directory holding all post.lg and opt files available for checking steps detail.
- **templates/**: Contains HTML templates using Jinja2 syntax.
  - **index.html**: Main HTML file rendered by Flask.
- **app.py**: Flask application script handling routing and API endpoints.
- **requirements.txt**: Lists all Python dependencies.
- **README.md**: Project documentation.

## API Integration

The application interacts with an API endpoint to fetch detailed information about each step. Here's an overview of the API interaction:

### Endpoint

- **URL**: `/get_step_detail`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Request Body**:

  ```json
  {
      "video": "video_name_without_extension",
      "step": step_number
  }
  ```

### Response

- **Success** (`status: "success"`):

  ```json
  {
      "status": "success",
      "merge_cell": "Merged Cell Information",
      "merge_cell_position": {
          "x": value,
          "y": value
      },
      "delete_cell": ["Cell1", "Cell2"],
      "number_of_move_cell": number,
      "move_cell": [
          {"name": "CellA", "x": value, "y": value},
          {"name": "CellB", "x": value, "y": value}
      ]
  }
  ```

- **Failure** (`status: "error"`):

  ```json
  {
      "status": "error",
      "message": "Error message detailing the issue."
  }
  ```

### API Usage

When a user opts to jump to a specific step or requests detailed information via the "Show Detail" checkbox, the frontend sends a POST request to `/get_step_detail` with the video name and step number. The backend processes this request, retrieves the relevant data, and responds with structured JSON, which the frontend then dynamically renders using Bootstrap tables.

*Note: Ensure the backend API is correctly implemented to handle these requests and return accurate data.*

## Customization

Optimize Step Visualization is designed to be flexible and easily customizable. Here are some areas you can tailor to fit specific needs:

### 1. **Add more feature**

- It welcome to add more feature!. 

### 2. **Styling Enhancements**

- Modify or extend the existing CSS in the `<style>` section of `index.html` or link an external stylesheet for more extensive changes.
- Customize Bootstrap components to match your preferred theme or branding.


## Acknowledgements

- **Bootstrap**: For providing a robust and responsive UI framework.
- **Flask**: For enabling quick and efficient backend development.
- **Developers and Contributors**: The open-source community for their invaluable tools and libraries.

---

*Feel free to reach out or open an issue if you have any questions or need assistance with the Optimize Step Visualization project!*
