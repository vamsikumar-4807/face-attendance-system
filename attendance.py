import cv2 # type: ignore
import pandas as pd # type: ignore
from datetime import datetime
import pickle
from typing import Dict, Set
import sys

ATTENDANCE_FILE = "attendance.csv"

def gen_frames():
    # Load trained model
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer/model.yml")

    # Load labels hg
    with open("trainer/labels.pickle", "rb") as f:
        labels = pickle.load(f)

    # Load / create attendance file
    try:
        attendance = pd.read_csv(ATTENDANCE_FILE)
    except:
        attendance = pd.DataFrame(columns=["Name", "Time"])
        attendance.to_csv(ATTENDANCE_FILE, index=False)

    cam = None
    for i in range(3):
        test = cv2.VideoCapture(i)
        if test.isOpened():
            cam = test
            print(f"✔ Using camera index: {i}")
            break

    if cam is None:
        print("❌ No camera found.")
        sys.exit(1)
        
    assert cam is not None

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    marked: Set[str] = set()
    recognition_buffer: Dict[str, int] = {}
    stable_name: str | None = None

    try:
        while True:
            ret, frame = cam.read()

            if not ret or frame is None:
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

                if conf < 95:   # RELAXED THRESHOLD TO FIX UNKNOWN ISSUE
                    name = labels.get(id_, "Unknown")

                    # Reset buffer for other names
                    for key in list(recognition_buffer.keys()):
                        if key != name:
                            recognition_buffer[key] = 0

                    recognition_buffer[name] = recognition_buffer.get(name, 0) + 1

                    # Accept only after 5 stable detections
                    if recognition_buffer.get(name, 0) >= 5: # type: ignore
                        stable_name = name
                else:
                    stable_name = "Unknown"

                # Display label
                display_label = stable_name if stable_name else "Detecting..."

                cv2.putText(frame, display_label, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (0, 255, 0) if stable_name != "Unknown" else (0, 0, 255), 2)

                cv2.rectangle(frame, (x, y), (x+w, y+h),
                              (0, 255, 0) if stable_name != "Unknown" else (0, 0, 255), 2)

                # -------- MARK ATTENDANCE --------
                if stable_name and stable_name != "Unknown" and stable_name not in marked:
                    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    attendance.loc[len(attendance)] = [stable_name, time_now]
                    attendance.to_csv(ATTENDANCE_FILE, index=False)
                    marked.add(stable_name)
                    print(f"✔ Marked: {stable_name}")

            # Yield frame directly to browser
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cam.release()

