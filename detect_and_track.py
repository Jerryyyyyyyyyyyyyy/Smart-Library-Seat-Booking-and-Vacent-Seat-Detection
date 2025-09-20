import cv2
import torch
import argparse
import numpy as np
from pathlib import Path
import mysql.connector
import os
import logging
from sort import *
from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, non_max_suppression, scale_coords
from utils.plots import plot_one_box
from utils.torch_utils import select_device, time_synchronized

# Setup logging
logging.basicConfig(filename='tracking.log', level=logging.INFO, format='%(asctime)s - %(message)s')

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

# Track occupation time
seat_occupation = {}  # seat_id: {'start_time': time, 'status': 'Occupied'}

def detect(opt):
    source, weights, view_img, imgsz, device = opt.source, opt.weights, opt.view_img, opt.img_size, opt.device
    save_img = not opt.nosave

    # Initialize
    device = select_device(device)
    model = attempt_load(weights, map_location=device)
    stride = int(model.stride.max())
    imgsz = check_img_size(imgsz, s=stride)

    # Dataloader
    dataset = LoadStreams(source, img_size=imgsz, stride=stride) if source.isnumeric() else LoadImages(source, img_size=imgsz)
    names = model.names

    # SORT tracker for persons
    person_tracker = Sort()

    for path, img, im0s, vid_cap in dataset:
        img = torch.from_numpy(img).to(device).float() / 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = model(img, augment=opt.augment)[0]
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes)

        for i, det in enumerate(pred):
            im0 = im0s[i].copy() if isinstance(im0s, list) else im0s

            if len(det):
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                person_dets = det[det[:, 5] == 0].cpu().numpy()  # Persons
                tracked_persons = person_tracker.update(person_dets)

                updates = []
                for seat_id, (x1, y1, x2, y2) in seats.items():
                    occupied = False
                    for person in tracked_persons:
                        px1, py1, px2, py2 = map(int, person[:4])
                        if max(px1, x1) < min(px2, x2) and max(py1, y1) < min(py2, y2):
                            occupied = True
                            break

                    cursor.execute("SELECT status FROM Seats WHERE seat_id=%s", (seat_id,))
                    current_status = cursor.fetchone()[0]
                    if current_status != "Booked":
                        new_status = "Occupied" if occupied else "Vacant"
                        updates.append((new_status, seat_id))
                        logging.info(f"Seat {seat_id} status: {new_status}")

                        if occupied:
                            if seat_id not in seat_occupation:
                                seat_occupation[seat_id] = {'start_time': time_synchronized(), 'status': 'Occupied'}
                            duration = time_synchronized() - seat_occupation[seat_id]['start_time']
                            label = f"Seat {seat_id}: Occupied ({duration:.1f}s)"
                        else:
                            seat_occupation.pop(seat_id, None)
                            label = f"Seat {seat_id}: Vacant"

                        color = (0, 0, 255) if occupied else (0, 255, 0)
                        plot_one_box([x1, y1, x2, y2], im0, label=label, color=color, line_thickness=2)

                if updates:
                    cursor.executemany("UPDATE Seats SET status=%s WHERE seat_id=%s", updates)
                    conn.commit()

            if view_img:
                cv2.imshow(str(path), im0)
                if cv2.waitKey(1) == ord('q'):
                    break

    cursor.close()
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, default='yolov7.pt', help='model.pt path')
    parser.add_argument('--source', type=str, default='0', help='source (0 for webcam)')
    parser.add_argument('--img-size', type=int, default=640, help='inference size')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold')
    parser.add_argument('--device', default='', help='cuda device or cpu')
    parser.add_argument('--view-img', action='store_true', help='display results')
    parser.add_argument('--nosave', action='store_true', help='do not save output')
    parser.add_argument('--classes', nargs='+', type=int, default=[0], help='filter classes (0 person)')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    opt = parser.parse_args()
    with torch.no_grad():
        detect(opt)