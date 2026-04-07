import cv2
import os
import numpy as np
from PIL import Image
import pickle

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

path = "dataset"

faces = []
ids = []
label_map = {}
current_id = 0

for person in os.listdir(path):

    person_dir = os.path.join(path, person)

    if not os.path.isdir(person_dir):
        continue

    label_map[current_id] = person

    for img in os.listdir(person_dir):

        img_path = os.path.join(person_dir, img)

        pil_img = Image.open(img_path).convert("L")
        img_np = np.array(pil_img, "uint8")

        # Detect face inside training image
        detected_faces = face_cascade.detectMultiScale(
            img_np,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80)
        )

        for (x, y, w, h) in detected_faces:
            face_region = img_np[y:y+h, x:x+w]
            faces.append(face_region)
            ids.append(current_id)

    current_id += 1

# Train model
recognizer.train(faces, np.array(ids))
recognizer.save("trainer/model.yml")

with open("trainer/labels.pickle", "wb") as f:
    pickle.dump(label_map, f)

print("✅ Training complete!")
