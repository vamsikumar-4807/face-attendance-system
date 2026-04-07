import cv2
import pandas as pd
from datetime import datetime
import pickle

ATTENDANCE_FILE = "attendance.csv"

# Load trained model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/model.yml")

# Load labels
with open("trainer/labels.pickle", "rb") as f:
    labels = pickle.load(f)

# Load / create attendance file
try:
    attendance = pd.read_csv(ATTENDANCE_FILE)
except:
    attendance = pd.DataFrame(columns=["Name", "Time"])
    attendance.to_csv(ATTENDANCE_FILE, index=False)

# -------- CAMERA SETUP --------
cam = None
for i in range(3):
    test = cv2.VideoCapture(i)
    if test.isOpened():
        cam = test
        print(f"✔ Using camera index: {i}")
        break

if cam is None:
    print("❌ No camera found.")
    quit()

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

marked = set()
recognition_buffer = {}
stable_name = None

print("Press Q to quit")

while True:
    ret, frame = cam.read()

    if not ret or frame is None:
        print("⚠️ Camera frame empty — retrying...")
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

        # DEBUG (optional)
        # print(f"Detected: {labels.get(id_, 'Unknown')} | Confidence: {conf}")

        if conf < 45:   # STRICT THRESHOLD
            name = labels[id_]

            # Reset buffer for other names
            for key in list(recognition_buffer.keys()):
                if key != name:
                    recognition_buffer[key] = 0

            recognition_buffer[name] = recognition_buffer.get(name, 0) + 1

            # Accept only after 5 stable detections
            if recognition_buffer[name] >= 5:
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
            time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            attendance.loc[len(attendance)] = [stable_name, time]
            attendance.to_csv(ATTENDANCE_FILE, index=False)
            marked.add(stable_name)
            print(f"✔ Marked: {stable_name}")

    cv2.imshow("Attendance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
