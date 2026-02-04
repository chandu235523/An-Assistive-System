import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import pyttsx3
import speech_recognition as sr
import cv2
import numpy as np
import time
from PIL import Image, ImageTk

stop_flag = False
mute_frame = None
listening_popup = None
deaf_frame = None
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

def blind_mode():
    global stop_flag
    stop_flag = False
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Unable to access the camera")
        return
    print("👁 Blind Mode Active - Obstacle Detection Started")
    previous_frame = None
    last_warning_time = 0
    cooldown = 4

    while not stop_flag:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if previous_frame is None:
            previous_frame = gray
            continue

        delta = cv2.absdiff(previous_frame, gray)
        thresh = cv2.threshold(delta, 30, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        close_obstacle = any(cv2.contourArea(c) > 1000 for c in contours)

        if close_obstacle and (time.time() - last_warning_time > cooldown):
            print("🚨 Obstacle within 50 cm!")
            tts_engine.say("Obstacle ahead . Please move.")
            tts_engine.runAndWait()
            last_warning_time = time.time()
        else:
            print("✅ Clear path")

        previous_frame = gray
        time.sleep(0.5)

    cap.release()
    print("👁 Blind Mode Stopped")

def deaf_mode(deaf_text_widget):
    global stop_flag, listening_popup
    stop_flag = False

    # Show the listening popup
    listening_popup = tk.Toplevel()
    listening_popup.title("Listening...")
    listening_popup.geometry("300x100")
    listening_popup.configure(bg="light yellow")
    tk.Label(listening_popup, text="🎧 Listening...", font=("Helvetica", 16, "bold"), bg="light yellow").pack(pady=20)
    listening_popup.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Please speak something...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        print("⏳ Recognizing...")
        text = recognizer.recognize_google(audio)
        print("✅ You said:", text)
        deaf_text_widget.delete("1.0", tk.END)
        deaf_text_widget.insert(tk.END, text)
    except sr.UnknownValueError:
        print("❌ Could not understand the audio.")
        deaf_text_widget.insert(tk.END, "[Could not understand the audio]")
    except sr.RequestError as e:
        print(f"⚠️ Error with the Google API: {e}")
        deaf_text_widget.insert(tk.END, "[API Error]")
    finally:
        if listening_popup:
            listening_popup.destroy()
            listening_popup = None
def show_alert(message):
    def popup():
        alert = tk.Tk()
        alert.withdraw()
        messagebox.showwarning("⚠ Alert", message)
        alert.destroy()
    threading.Thread(target=popup).start()
def voice_command_listener():
    import speech_recognition as sr
    global root, mute_frame, deaf_frame

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🎙️ Voice Command Listener Active...")

    while True:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            print("🕐 Listening for command...")
            audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio).lower()
            print("🎤 Voice command:", command)

            if "start blind mode" in command:
                root.after(0, lambda: threading.Thread(target=blind_mode).start())

            elif "start deaf mode" in command:
                root.after(0, show_deaf_box)

            elif "start mute mode" in command:
                root.after(0, show_mute_box)

            elif "stop activity" in command:
                root.after(0, stop_activity)

        except Exception as e:
            print(f"❌ Error: {e}")

def show_mute_box():
    global mute_frame
    if mute_frame:
        mute_frame.pack(pady=5)

def show_deaf_box():
    global deaf_frame, deaf_text
    if deaf_frame:
        deaf_frame.pack(pady=5)
        threading.Thread(target=lambda: deaf_mode(deaf_text)).start()

def start_mute_mode(input_box):
    global stop_flag
    stop_flag = False
    text = input_box.get("1.0", tk.END).strip()
    if text:
        print(f"🗣 Speaking: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()

def stop_activity():
    global stop_flag, mute_frame, deaf_frame, listening_popup
    stop_flag = True
    if mute_frame:
        mute_frame.pack_forget()
    if deaf_frame:
        deaf_frame.pack_forget()
    if listening_popup:
        listening_popup.destroy()
        listening_popup = None
    print("🛑 All activities stopped.")
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import scrolledtext
import threading

def launch_gui():
    global mute_frame, deaf_frame, mute_input, deaf_text, root

    root = tk.Tk()
    root.geometry("1000x700")
    root.title("TRISVA - Assistive System")
    root.configure(bg="#0f2c3e")  # Dark background

    # === Logo ===
    try:
        logo_img = Image.open(r"c:\Users\cheta\Downloads\11zon_cropped.png")  # Replace with your logo file
        logo_img = logo_img.resize((200, 200))
        logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo, bg="#0f2c3e")
        logo_label.image = logo
        logo_label.pack(pady=(20, 5))
    except Exception as e:
        print("Logo not loaded:", e)

    # === Title ===
    tk.Label(root, text="Trisva-Assistive System", font=("Helvetica", 31, "bold"), fg="#3daeff", bg="#0f2c3e").pack(pady=(0, 30))
    #tk.Label(root, text="-Assistive System", font=("Helvetica",, "bold"), fg="#3daeff", bg="#0f2c3e").pack(pady=(0, 30))
    # === Mode Buttons in Horizontal Frame ===
    mode_frame = tk.Frame(root, bg="#0f2c3e")
    mode_frame.pack(pady=10)

    def create_mode_card(title, button_text, command, color):
        card = tk.Frame(mode_frame, bg="#142c47", bd=2, relief="solid", highlightthickness=2, highlightbackground="#3daeff")
        card.configure(width=250, height=180)
        card.pack_propagate(False)

        tk.Label(card, text=title, font=("Helvetica", 18, "bold"), fg="white", bg="#142c47").pack(pady=(20, 10))
        tk.Button(card, text=button_text, font=("Helvetica", 14), bg=color, fg="white",
                  activebackground=color, activeforeground="white", padx=10, pady=5,
                  relief="flat", command=command).pack()

        card.pack(side="left", padx=20)

    # === Cards ===
    create_mode_card("Blind Mode", "Activate", lambda: threading.Thread(target=blind_mode).start(), "#32aaff")
    create_mode_card("Deaf Mode", "Activate", show_deaf_box, "#32aaff")
    create_mode_card("Mute Mode", "Activate", show_mute_box, "#32aaff")

    # === Deaf Mode Box ===
    deaf_frame = tk.Frame(root, bg="white", pady=10)
    deaf_text = scrolledtext.ScrolledText(deaf_frame, width=50, height=4, font=("Helvetica", 12))
    deaf_text.pack()

    # === Mute Mode Box ===
    mute_frame = tk.Frame(root, bg="white", pady=10)
    mute_input = scrolledtext.ScrolledText(mute_frame, width=50, height=4, font=("Helvetica", 12))
    mute_input.pack()
    tk.Button(mute_frame, text="Speak Text", font=("Helvetica", 14), bg="#3daeff", fg="white",
              command=lambda: start_mute_mode(mute_input)).pack(pady=10)

    # === Stop Button at Bottom ===
    stop_btn_frame = tk.Frame(root, bg="#0f2c3e")
    stop_btn_frame.pack(pady=40)
    tk.Button(stop_btn_frame, text="Stop Activity", font=("Helvetica", 14, "bold"),
              bg="#ff4d4d", fg="white", activebackground="#e33", activeforeground="white",
              padx=20, pady=8, relief="flat", command=stop_activity).pack()

    threading.Thread(target=voice_command_listener, daemon=True).start()
    root.mainloop()

# === Launch the GUI ===
if __name__ == "__main__":
    launch_gui()