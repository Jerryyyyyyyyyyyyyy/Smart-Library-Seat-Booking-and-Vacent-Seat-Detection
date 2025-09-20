# Smart Library Seat Booking System

A real-time seat occupancy detection and booking system for libraries, built with Flask, OpenCV, YOLOv7, and MySQL. It uses a laptop webcam to detect seat occupancy and allows users to book seats via a web interface with a vibrant, user-friendly design.

## Features

- **Real-Time Detection**: Detects seat occupancy using a laptop webcam with two methods:
  - Fixed seat detection (`seat_detector.py`) using predefined coordinates and pixel intensity.
  - Dynamic detection (`detect_and_track.py`) using YOLOv7 and SORT for person tracking.
- **Web Interface**: Flask-based app with:
  - Login system for user authentication.
  - Interactive seat map (`/map`) showing real-time seat status (Vacant/Occupied).
  - Vibrant text and transparent header for a modern look.
- **Database Integration**: MySQL stores seat statuses (`library` database, `Seats` table).
- **Scalable**: Easily adaptable to other video sources (e.g., IP cameras).

## Prerequisites

- **Hardware**: Laptop with a webcam (macOS, Windows, or Linux).
- **Software**:
  - Python 3.8+
  - MySQL Server
  - Git
- **Dependencies**: Listed in `requirements.txt` (install via `pip install -r requirements.txt`).

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Jerryyyyyyyyyyyyyy/Library-Seat-Occupancy-Detection-main 2.git
   cd Library-Seat-Occupancy-Detection-main 2
   ```

2. **Set Up Virtual Environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # Or: venv\Scripts\activate  # On Windows
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up MySQL Database**:

   - Start MySQL server:

     ```bash
     mysql.server start  # On macOS
     # Or: sudo systemctl start mysql  # On Linux
     ```
   - Create the `library` database and `Seats` table:

     ```sql
     mysql -u root -p
     CREATE DATABASE library;
     USE library;
     CREATE TABLE Seats (
         seat_id INT PRIMARY KEY,
         status VARCHAR(20),
         x1 INT,
         y1 INT,
         x2 INT,
         y2 INT
     );
     INSERT INTO Seats (seat_id, status, x1, y1, x2, y2) VALUES
         (1, 'Vacant', 100, 100, 200, 200),
         (2, 'Vacant', 300, 100, 400, 200);
     ```

5. **Configure Environment Variables**:

   - Create a `.env` file in the project root:

     ```
     DB_PASS=your-mysql-password
     ```
   - Replace `your-mysql-password` with your MySQL root password.

6. **Position Webcam**:

   - Point your laptop’s webcam at the library seats to capture the area of interest.
   - Adjust seat coordinates in `seat_detector.py` (or `detect_and_track.py`) to match the webcam’s view.

## Usage

1. **Run Detection Script** (Choose one):

   - **Fixed Seat Detection** (simpler, faster):

     ```bash
     python3 seat_detector.py
     ```
     - Displays webcam feed with seat overlays (green for Vacant, red for Occupied).
     - Updates `Seats` table in MySQL.
   - **Dynamic Detection** (YOLOv7-based, more accurate):

     ```bash
     python3 detect_and_track.py --view-img
     ```
     - Requires `yolov7.pt` (download from YOLOv7 repo).
     - Tracks people and updates seat statuses dynamically.

2. **Run Flask App**:

   ```bash
   python3 app.py
   ```

   - Open `http://127.0.0.1:5000` in a browser.
   - Log in to access the seat map (`/map`) and book seats.
   - Seat statuses update in real-time based on webcam detection.

3. **Stop Scripts**:

   - Press `q` in the detection window to exit.
   - Use `Ctrl+C` in the terminal to stop the Flask app.

## Project Structure

```
library-seat-occupancy-detection/
├── app.py                # Flask web application
├── seat_detector.py      # Fixed seat detection using webcam
├── detect_and_track.py   # Dynamic detection using YOLOv7
├── templates/
│   ├── home.html         # Login page
│   ├── index.html        # Seat map page
├── .env                  # Environment variables (DB_PASS)
├── requirements.txt      # Python dependencies
├── yolov7.pt             # YOLOv7 model weights (for detect_and_track.py)
```

## Troubleshooting

- **Webcam Issues**:
  - Ensure no other app is using the webcam.
  - Test webcam:

    ```bash
    python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
    ```
  - On macOS, check camera permissions (System Preferences &gt; Security & Privacy &gt; Camera).
- **Database Errors**:
  - Verify `.env` has the correct `DB_PASS`.
  - Ensure MySQL is running:

    ```bash
    mysqladmin -u root -p ping
    ```
- **No Detections**:
  - Adjust seat coordinates in `seat_detector.py` to match webcam view.
  - For `detect_and_track.py`, ensure `yolov7.pt` is in the project root.
- **Flask Issues**:
  - Check `/seats` endpoint:

    ```bash
    curl http://127.0.0.1:5000/seats
    ```

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature"`.
4. Push to the branch: `git push origin feature-name`.
5. Submit a pull request.

## License

MIT License. See LICENSE for details.