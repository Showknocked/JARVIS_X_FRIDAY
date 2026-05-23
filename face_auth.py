import os
import cv2
import requests
import json
import numpy as np

CASCADE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
CASCADE_FILE = "haarcascade_frontalface_default.xml"
DATASET_DIR = "dataset"
TRAINER_FILE = "trainer.yml"

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {"BYPASS_PIN": "1111"}

def download_cascade():
    """Dynamically downloads Haar Cascade classification files if missing locally."""
    if not os.path.exists(CASCADE_FILE):
        print("[System]: Downloading Haar Cascade model from OpenCV...")
        try:
            r = requests.get(CASCADE_URL, timeout=10)
            with open(CASCADE_FILE, "wb") as f:
                f.write(r.content)
            print("[System]: Haar Cascade successfully downloaded.")
        except Exception as e:
            print(f"[Error]: Cascade acquisition failed: {e}")

def get_face_recognizer():
    """Checks for opencv-contrib-python LBPH bindings to prevent library crashes."""
    try:
        return cv2.face.LBPHFaceRecognizer_create()
    except AttributeError:
        return None

def generate_dataset():
    """Captures facial data using macOS default web camera."""
    download_cascade()
    detector = cv2.CascadeClassifier(CASCADE_FILE)
    cam = cv2.VideoCapture(0)
    
    if not cam.isOpened():
        print("[Error]: Webcam access blocked. Verify macOS Security & Privacy Camera permissions.")
        return False
        
    print("[System]: Scanning Face. Look directly at your camera...")
    
    if not os.path.exists(DATASET_DIR):
        os.makedirs(DATASET_DIR)
        
    count = 0
    while True:
        ret, img = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            count += 1
            face_img = gray[y:y+h, x:x+w]
            cv2.imwrite(f"{DATASET_DIR}/User.{count}.jpg", face_img)
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.waitKey(50)
            
        cv2.imshow("Registering biometric dataset (ESC to close)", img)
        k = cv2.waitKey(100) & 0xff
        if k == 27 or count >= 30:
            break
            
    cam.release()
    cv2.destroyAllWindows()
    print(f"[System]: Face registration completed. Saved to {DATASET_DIR}.")
    return True

def train_model():
    """Builds and trains local facial recognition matrix."""
    recognizer = get_face_recognizer()
    if recognizer is None:
        print("[Error]: LBPH Recognizer modules not found. Defaulting to bypass code.")
        return False
        
    detector = cv2.CascadeClassifier(CASCADE_FILE)
    if not os.path.exists(DATASET_DIR) or len(os.listdir(DATASET_DIR)) == 0:
        print("[Error]: Biometric dataset not built. Run initialization steps.")
        return False
        
    print("[System]: Calibrating user credentials database...")
    image_paths = [os.path.join(DATASET_DIR, f) for f in os.listdir(DATASET_DIR) if f.endswith(".jpg")]
    face_samples = []
    ids = []
    
    for path in image_paths:
        gray_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        try:
            user_id = int(os.path.split(path)[-1].split(".")[1])
        except (ValueError, IndexError):
            user_id = 1
        
        faces = detector.detectMultiScale(gray_img)
        for (x, y, w, h) in faces:
            face_samples.append(gray_img[y:y+h, x:x+w])
            ids.append(user_id)
            
    recognizer.train(face_samples, np.array(ids))
    recognizer.write(TRAINER_FILE)
    print(f"[System]: Biometric settings optimized and saved to {TRAINER_FILE}.")
    return True

def authenticate_user():
    """Authenticates the user using biometric scanning or passcode override."""
    config_data = get_config()
    bypass_pin = config_data.get("BYPASS_PIN", "1111")
    
    recognizer = get_face_recognizer()
    if recognizer is None or not os.path.exists(TRAINER_FILE):
        pin_input = input("Biometric data unconfigured. Enter bypass PIN to continue: ")
        return pin_input == bypass_pin

    download_cascade()
    face_cascade = cv2.CascadeClassifier(CASCADE_FILE)
    recognizer.read(TRAINER_FILE)
    
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        pin_input = input("Web camera blocked. Enter bypass PIN to continue: ")
        return pin_input == bypass_pin
        
    print("[System]: Scanning face profile...")
    authenticated = False
    scans = 0
    
    while scans < 30:
        ret, img = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        
        for (x, y, w, h) in faces:
            id_num, score = recognizer.predict(gray[y:y+h, x:x+w])
            if score < 65:  # High confidence match threshold
                authenticated = True
                break
                
        if authenticated:
            break
        scans += 1
        cv2.waitKey(100)
        
    cam.release()
    cv2.destroyAllWindows()
    
    if authenticated:
        print("[System]: Secure authorization confirmed.")
        return True
    else:
        print("[System]: Biometric profile did not match.")
        pin_input = input("Enter Security PIN to bypass: ")
        return pin_input == bypass_pin