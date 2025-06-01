import RPi.GPIO as GPIO
import time
import requests
import cv2
import numpy as np
from picamera import PiCamera
from firebase import firebase

# Firebase setup
FIREBASE_URL = "https://your-firebase-url.firebaseio.com/"
firebase = firebase.FirebaseApplication(FIREBASE_URL, None)

# GPIO Pin setup
TURBIDITY_PIN = 17
UV_LED_PIN = 18
BUZZER_PIN = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(TURBIDITY_PIN, GPIO.IN)
GPIO.setup(UV_LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Camera Setup
camera = PiCamera()
camera.resolution = (640, 480)

def read_turbidity():
    return GPIO.input(TURBIDITY_PIN)  # HIGH: Clear, LOW: Turbid

def capture_uv_fluorescence():
    GPIO.output(UV_LED_PIN, GPIO.HIGH)
    time.sleep(1)
    camera.capture('/home/pi/image.jpg')
    GPIO.output(UV_LED_PIN, GPIO.LOW)
    return '/home/pi/image.jpg'

def analyze_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    particle_count = cv2.countNonZero(thresh)
    return particle_count

def send_to_firebase(data):
    firebase.post('/microplastic_data', data)

def alert():
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

def main():
    while True:
        turbidity = read_turbidity()
        print(f"Turbidity: {'High' if turbidity == 0 else 'Low'}")
        
        img_path = capture_uv_fluorescence()
        particles = analyze_image(img_path)
        print(f"Microplastic Particles Detected: {particles}")

        data = {
            'timestamp': time.ctime(),
            'turbidity': 'High' if turbidity == 0 else 'Low',
            'particle_count': particles
        }
        send_to_firebase(data)

        if particles > 100:  # Customize threshold
            alert()

        time.sleep(60)

try:
    main()
except KeyboardInterrupt:
    GPIO.cleanup()
    print("Program stopped.")
