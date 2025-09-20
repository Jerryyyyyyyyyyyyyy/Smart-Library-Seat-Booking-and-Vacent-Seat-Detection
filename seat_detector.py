import cv2
import torch
import mysql.connector
import os
import logging

# Setup logging
logging.basicConfig(filename='detection.log', level=logging.INFO, format='%(asctime)s - %(message)s')

try:
    # MySQL connection
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASS", "yourpassword"),
        database="library"
    )
    cursor = conn.cursor()

    # Fetch seat positions
    cursor.execute("SELECT seat_id, x1, y1, x2, y2 FROM Seats")
    seats = {row[0]: (row[1], row[2], row[3], row[4]) for row in cursor.fetchall()}

    # Load YOLOv5 model
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    model.eval()

    # Video feed
    cap = cv2.VideoCapture(0)  # Replace with RTSP URL if needed
    if not cap.isOpened():
        logging.error("Failed to open video feed")
        raise Exception("Camera not accessible")

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to capture frame")
            break

        results = model(frame)
        detections = results.xyxy[0].cpu().numpy()

        updates = []
        for seat_id, (x1, y1, x2, y2) in seats.items():
            occupied = False
            for *box, conf, cls in detections:
                if int(cls) == 0:  # Person
                    bx1, by1, bx2, by2 = box
                    if bx1 < x2 and bx2 > x1 and by1 < y2 and by2 > y1:
                        occupied = True
                        break

            cursor.execute("SELECT status FROM Seats WHERE seat_id=%s", (seat_id,))
            current_status = cursor.fetchone()[0]
            if current_status != "Booked":
                new_status = "Occupied" if occupied else "Vacant"
                updates.append((new_status, seat_id))
                logging.info(f"Seat {seat_id} status: {new_status}")

            # Draw
            color = (0, 255, 0) if current_status == "Vacant" else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"Seat {seat_id}: {current_status}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Batch update
        if updates:
            cursor.executemany("UPDATE Seats SET status=%s WHERE seat_id=%s", updates)
            conn.commit()

        cv2.imshow("Library Seat Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    logging.error(f"Error: {e}")
finally:
    cap.release()
    cv2.destroyAllWindows()
    cursor.close()
    conn.close()