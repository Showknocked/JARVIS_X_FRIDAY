import os
import subprocess
import json
import speech_recognition as sr

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {
        "JARVIS_VOICE": "Daniel",
        "FRIDAY_VOICE": "Samantha",
        "DEFAULT_MODE": "JARVIS",
        "SPEECH_RATE": 175
    }

config = load_config()

class AssistantVoice:
    def __init__(self):
        self.mode = config.get("DEFAULT_MODE", "JARVIS")
        self.jarvis_voice = config.get("JARVIS_VOICE", "Daniel")
        self.friday_voice = config.get("FRIDAY_VOICE", "Samantha")
        self.rate = config.get("SPEECH_RATE", 175)
        self.recognizer = sr.Recognizer()
        
    def set_mode(self, mode):
        if mode.upper() in ["JARVIS", "FRIDAY"]:
            self.mode = mode.upper()
            return True
        return False

    def get_voice(self):
        return self.jarvis_voice if self.mode == "JARVIS" else self.friday_voice

    def get_greeting_prefix(self):
        return "Yes, Sir." if self.mode == "JARVIS" else "Yes, Boss."

    def speak(self, text):
        """
        Uses native macOS 'say' system command. Extremely lightweight,
        avoids the PyObjC threading bugs associated with pyttsx3.
        """
        voice = self.get_voice()
        print(f"[{self.mode}]: {text}")
        try:
            subprocess.run(["say", "-v", voice, "-r", str(self.rate), text], check=True)
        except Exception:
            # Fallback prints safely if voice utilities hit execution errors
            pass

    def listen(self):
        """
        Listens via SpeechRecognition. Fallback ensures the program continues
        even if PyAudio is missing or microphone permissions are blocked.
        """
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
                print(f"\nListening ({self.mode})...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                print("Processing speech...")
                query = self.recognizer.recognize_google(audio, language="en-US")
                print(f"You (Voice): {query}")
                return query.lower()
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            return ""
        except Exception:
            print("\n[Microphone warning or PyAudio missing. Switching to terminal input mode]")
            query = input("You (Text): ")
            return query.lower()