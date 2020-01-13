import cv2
import numpy as np
import time
import imutils
import math


# Ham detect car và bus tu anh input
def get_object(net, image, conf_threshold=0.5, H=360, W=460):
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()
    boxes = []
    CLASSES = ["_", "_", "_", "_", "_","_", "bus", "car", "_", "_", "_", "_", "_", "_", "_", "_", "_", "_", "_", "_", "_"]
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            idx = int(detections[0, 0, i, 1])
            if CLASSES[idx] == 'car' or CLASSES[idx] == 'bus':
                box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                (startX, startY, endX, endY) = box.astype("int")
                box = [startX, startY, endX - startX, endY - startY]
                boxes.append(box)

    return image, boxes

# Define cac tham soR

prototype_url = 'models/MobileNetSSD_deploy.prototxt'
model_url = 'models/MobileNetSSD_deploy.caffemodel'
video_path = 'test.mp4'


max_distance = 50
input_h = 360
input_w = 460
laser_line = input_h - 50

net = cv2.dnn.readNetFromCaffe(prototype_url, model_url)
cap = cv2.VideoCapture(video_path)

# define a box of Roid
frame_number = 0
car_number = 0
obj_cnt = 0
trackers = []

while cap.isOpened():

    laser_line_color = (0, 0, 255)
    boxes = []

    # Doc anh tu video
    _, frame = cap.read()
    if frame is None:
        break

    # Resize nho lai
    frame = cv2.resize(frame, (input_w, input_h))

    # Duyet qua cac doi tuong trong tracker
    old_trackers = trackers
    trackers = []

    for obj in old_trackers:

        # Update tracker
        tracker = obj['tracker']
        (success, box) = tracker.update(frame)
        boxes.append(box)

        new_obj = dict()
        new_obj['ID'] = obj['ID']
        new_obj['tracker'] = tracker


        # Tinh toan tam doi tuong
        (x, y, w, h) = [int(v) for v in box]
        center_X = int((x + (x + w)) / 2.0)
        center_Y = int((y + (y + h)) / 2.0)

        # Ve hinh chu nhat quanh doi tuong
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Ve hinh tron tai tam doi tuong
        cv2.circle(frame, (center_X, center_Y), 4, (0, 255, 0), -1)

        # So sanh tam doi tuong voi duong laser line
        if center_Y > laser_line:
            # Neu vuot qua thi khong track nua ma dem xe
            laser_line_color = (0, 255, 255)
            car_number += 1
        else:
            # Con khong thi track tiep
            trackers.append(new_obj)

    # Thuc hien object detection moi 5 frame
    if frame_number % 5 == 0:
        # Detect doi tuong
        frame, boxes_detected = get_object(net, frame)

        for box_dt in boxes_detected:
            old_obj = False

            (xd, yd, wd, hd) = [int(v) for v in box_dt]
            center_Xd = int((xd + (xd + wd)) / 2.0)
            center_Yd = int((yd + (yd + hd)) / 2.0)

            if  center_Yd <= laser_line - max_distance:

                # Duyet qua cac box, neu sai lech giua doi tuong detect voi doi tuong da track ko qua max_distance thi coi nhu 1 doi tuong
                for box_tracker in boxes:
                    (xt, yt, wt, ht) = [int(c) for c in box_tracker]
                    center_Xt = int((xt + (xt + wt)) / 2.0)
                    center_Yt = int((yt + (yt + ht)) / 2.0)
                    distance = math.sqrt((center_Xt - center_Xd) ** 2 + (center_Yt - center_Yd) ** 2)

                    if distance < max_distance:
                        old_obj = True
                        break

                # Neu khong phai la doi tuong da track
                if not old_obj:

                    cv2.rectangle(frame, (xd, yd), ((xd + wd), (yd + hd)), (0, 0, 255), 2)
                    # Tao doi tuong tracker moi

                    tracker = cv2.TrackerKCF_create()

                    obj_cnt += 1

                    new_obj = dict()
                    tracker.init(frame, tuple(box_dt))
                    new_obj['ID'] = obj_cnt
                    new_obj['tracker'] = tracker

                    trackers.append(new_obj)

    # Tang frame
    frame_number += 1

    # Hien thi so xe
    text = " Car number: " + "{:d}".format(car_number)
    cv2.putText(frame, text, (10, input_h - ((1 * 20) + 300)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw laser line
    cv2.line(frame, (0, laser_line), (input_w, laser_line), laser_line_color, 2)
    cv2.putText(frame, "Laser line", (10, laser_line-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, laser_line_color, 2)

    # Frame
    cv2.imshow("Image", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows