from flask import Flask, render_template, request, jsonify
import ollama
import pyttsx3
import os
import webbrowser
import cv2
import datetime
import time
import queue
import threading
import speech_recognition as sr
app = Flask(__name__)
# Queue for speech requests
speech_queue = queue.Queue()
camera_running = False  # Flag to track camera state
camera_thread = None  # Thread reference
cap=None
def speak_text(text):
    """ Add text to the speech queue for processing. """
    speech_queue.put(text)
def speech_worker():
    """ Continuously process speech requests from the queue. """
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    # Set voice to female (index 1)
    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)
    engine.setProperty("rate", 150)  # Adjust speech speed
    while True:
        text = speech_queue.get()
        if text is None:
            break  # Exit loop when None is received
        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()
# Start speech processing in a separate thread
speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()
# Function to open applications
def open_application(command):
    if "google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google"
    elif "youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"
    elif "notepad" in command:
        os.system("notepad")
        return "Opening Notepad"
    elif "whatsapp" in command:
        os.system("start shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App")
        return "Opening WhatsApp"
    elif "calculator" in command:
        os.system("calc")
        return "Opening Calculator"
    elif "camera" in command:
        return start_camera_thread()
    elif "close camera" in command:
        return stop_camera()
    return None
# Function to open the camera
def open_camera():
    """Function to start the camera."""
    global camera_running, cap
    if camera_running:
        print("Camera is already running.")
        return
    camera_running = True
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        camera_running = False
        return
    print("Camera started. Press 'q' to close.")
    while camera_running:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Camera", frame)
        # Press 'q' to close the camera window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_camera()
            break
    cap.release()
    cv2.destroyAllWindows()
def start_camera_thread():
    """Function to start the camera in a separate thread."""
    global camera_running, camera_thread
    if camera_running:
        return "Camera is already running."
    camera_thread = threading.Thread(target=open_camera, daemon=True)
    camera_thread.start()
    return "Camera started."
def stop_camera():
    """Function to properly stop the camera."""
    global camera_running, cap
    if not camera_running:
        return "Camera is not running."
    camera_running = False  # Stop loop
    time.sleep(1)  # Allow time for the camera loop to exit
    if cap is not None:
        cap.release()  # Release camera resource
    cv2.destroyAllWindows()
    return "Camera closed."
# Function to get the current time
def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")
# Function to control the system
def system_control(command):
    if "shutdown" in command:
        os.system("shutdown /s /t 5")
        return "Shutting down the system in 5 seconds."
    elif "restart" in command:
        os.system("shutdown /r /t 5")
        return "Restarting the system in 5 seconds."
    return None
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"].lower()
    # Check for application commands
    app_response = open_application(user_message)
    if app_response:
        speak_text(app_response)
        return jsonify({"response": app_response})
    # Check for system control commands
    sys_response = system_control(user_message)
    if sys_response:
        speak_text(sys_response)
        return jsonify({"response": sys_response})
    # Check for time retrieval
    if "time" in user_message:
        time_now = get_current_time()
        speak_text(f"The current time is {time_now}")
        return jsonify({"response": f"The current time is {time_now}"})
    # Default to AI chat response using Ollama
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": user_message}])
    bot_reply = response['message']['content'] if 'message' in response else "I'm not sure how to respond."
    # Speak the response
    speak_text(bot_reply)
    return jsonify({"response": bot_reply})
if __name__ == "__main__":
    app.run(debug=True)
