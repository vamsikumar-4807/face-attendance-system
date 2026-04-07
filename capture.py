import cv2
import os

name = input("Enter person name: ")

path = f"dataset/{name}"
os.makedirs(path, exist_ok=True)
cam = cv2.VideoCapture(0)
count = 0

print("Capturing images... Look at the camera. Press Q to stop early.")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        count += 1
        cv2.imwrite(f"{path}/{count}.jpg", gray[y:y+h, x:x+w])
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

    cv2.imshow("Capturing", frame)

    if cv2.waitKey(1) & 0xFF == ord('q') or count >= 40:
        break

cam.release()
cv2.destroyAllWindows()

print("Done capturing!")
