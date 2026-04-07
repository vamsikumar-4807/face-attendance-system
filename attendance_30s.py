import cv2
import pandas as pd
from datetime import datetime
import time
import pickle

ATTENDANCE_FILE = "attendance.csv"

# =====================================
# RESET ATTENDANCE FILE EVERY RUN
# =====================================

attendance = pd.DataFrame(columns=["name", "time"])
attendance.to_csv(ATTENDANCE_FILE, index=False)

# =====================================
# LOAD TRAINED MODEL
# =====================================

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/model.yml")

with open("trainer/labels.pickle", "rb") as f:
    labels = pickle.load(f)

# =====================================
# CAMERA SETUP
# =====================================

cam = cv2.VideoCapture(0)

if not cam.isOpened():
    print("❌ Camera not found")
    exit()

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Bring window to front
cv2.namedWindow("Attendance (30s)", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Attendance (30s)", cv2.WND_PROP_TOPMOST, 1)

marked = set()
recognition_buffer = {}

print("🎥 Attendance running for 30 seconds...")
start_time = time.time()

# =====================================
# FACE DETECTION LOOP
# =====================================

while True:

    if time.time() - start_time >= 30:
        print("⏱️ Time over — stopping camera.")
        break

    ret, frame = cam.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:

        id_, conf = recognizer.predict(gray[y:y+h, x:x+w])

        # Safety check
        if id_ in labels:
            detected_name = labels[id_]
        else:
            detected_name = "Unknown"

        # =====================================
        # STRICT THRESHOLD (IMPORTANT)
        # =====================================
        if conf < 95:   # STRICTER VALUE
            name = detected_name

            # Increase stability counter
            recognition_buffer[name] = recognition_buffer.get(name, 0) + 1

            # Mark only after 5 stable detections
            if recognition_buffer[name] >= 5 and name not in marked:

                time_now = datetime.now().strftime("%d-%m-%Y %I:%M %p")

                attendance.loc[len(attendance)] = [name, time_now]
                attendance.to_csv(ATTENDANCE_FILE, index=False)

                marked.add(name)
                print(f"✔ Marked Present: {name}")

        else:
            name = "Unknown"

        # Show only name (no confidence)
        cv2.putText(
            frame,
            name,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0,255,0),
            2
        )

        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0,255,0),
            2
        )

    cv2.imshow("Attendance (30s)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()

print("📷 Camera closed.")

# =====================================
# CALL MAIL SYSTEM
# =====================================

print("➡ Calling mail system...")

import mail_notify

absentee_names = mail_notify.send_mails()

# =====================================
# PRINT FOR FLASK
# =====================================

print("ABSENTEES_START")
print(",".join(absentee_names))
print("ABSENTEES_END")
