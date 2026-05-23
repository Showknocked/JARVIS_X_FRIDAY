import os
import sys
from voice_engine import AssistantVoice
import face_auth
import features

def display_banner():
    banner = """
==================================================
           J.A.R.V.I.S  x  F.R.I.D.A.Y
               Integrated Assistant
                 Optimized for macOS
==================================================
    """
    print(banner)

def main():
    display_banner()
    
    # 1. Setup Face ID model database if missing
    if not os.path.exists(face_auth.TRAINER_FILE):
        print("[Setup Notice]: Biometric profile has not been trained yet.")
        choice = input("Register your facial structure now? (yes/no): ").strip().lower()
        if choice in ["yes", "y"]:
            if face_auth.generate_dataset():
                face_auth.train_model()
        else:
            print("[System]: Continuing with security bypass mode.")

    # 2. Run verification pipeline
    if not face_auth.authenticate_user():
        print("[Security Event]: Authentication failed. Terminating system.")
        sys.exit(1)
        
    # 3. Instantiate Engine & Voice Profiles
    assistant = AssistantVoice()
    mode = assistant.mode
    prefix = assistant.get_greeting_prefix()
    assistant.speak(f"Biometrics verified. System fully operational. {prefix} I am {mode}. Ready to manage your pipeline.")

    while True:
        query = assistant.listen()
        
        if not query:
            continue
            
        print(f"Recognized input: {query}")
        
        # Termination
        if any(cmd in query for cmd in ["exit", "shutdown", "terminate", "quit"]):
            prefix = assistant.get_greeting_prefix()
            recipient = "Sir" if assistant.mode == "JARVIS" else "Boss"
            assistant.speak(f"Shutting down core protocols. Goodbye, {recipient}.")
            break

        # Assistant Personalities Swapping Controls
        elif "switch to friday" in query or "activate friday" in query:
            assistant.set_mode("FRIDAY")
            assistant.speak("Systems loaded. Good day, Boss. I am Friday, active and online.")
            continue
            
        elif "switch to jarvis" in query or "activate jarvis" in query:
            assistant.set_mode("JARVIS")
            assistant.speak("Database synced. Excellent choice, Sir. Jarvis is back online.")
            continue

        # Date & Time Queries
        elif "time" in query or "date" in query or "day" in query:
            assistant.speak(features.get_date_time())

        # Wikipedia queries
        elif "wikipedia" in query or "search for" in query:
            term = query.replace("wikipedia", "").replace("search for", "").strip()
            if term:
                assistant.speak(features.search_wikipedia(term))
            else:
                assistant.speak("What search term should I look up on Wikipedia?")

        # Dictionary Query
        elif "dictionary" in query or "define" in query or "meaning of" in query:
            word = query.replace("dictionary", "").replace("define", "").replace("meaning of", "").strip()
            if word:
                assistant.speak(features.search_dictionary(word))
            else:
                assistant.speak("Please say the word you want defined.")

        # News Search
        elif "news" in query or "headlines" in query:
            assistant.speak("Syncing with news feeds...")
            assistant.speak(features.fetch_news())

        # Weather query
        elif "weather" in query or "temperature" in query:
            words = query.split()
            city = ""
            if "in" in words:
                idx = words.index("in")
                if idx + 1 < len(words):
                    city = " ".join(words[idx+1:])
            assistant.speak(features.fetch_weather(city))

        # Geolocation query
        elif "location" in query or "where am i" in query or "coordinates" in query:
            assistant.speak(features.get_current_location())

        # Task/Todo List Module
        elif "todo" in query or "task list" in query:
            if "add" in query or "insert" in query:
                task = query.replace("add", "").replace("to my todo", "").replace("todo", "").replace("task list", "").strip()
                assistant.speak(features.manage_todo("add", task))
            elif "clear" in query or "delete" in query:
                assistant.speak(features.manage_todo("clear"))
            else:
                assistant.speak(features.manage_todo("read"))

        # URL Navigation and Browser Searches
        elif "open" in query or "search google for" in query:
            site = query.replace("open", "").replace("search google for", "").strip()
            if site:
                assistant.speak(features.open_website(site))
            else:
                assistant.speak("Specify the website or query to load.")

        # Diagnostics metrics
        elif "diagnostics" in query or "system status" in query or "battery status" in query or "cpu" in query:
            assistant.speak(features.get_system_diagnostics())

        # macOS volume controller
        elif "volume" in query:
            numbers = [int(s) for s in query.split() if s.isdigit()]
            if numbers:
                vol_level = numbers[0]
                if 0 <= vol_level <= 100:
                    assistant.speak(features.adjust_system_volume(vol_level))
                else:
                    assistant.speak("Provide a level between zero and one hundred.")
            else:
                assistant.speak("What level percentage should I adjust the system volume to?")

        # Media downloader
        elif "download video" in query or "download youtube" in query:
            assistant.speak("Please supply your URL in your terminal now.")
            url_input = input("Enter target URL: ").strip()
            assistant.speak(features.download_youtube_video(url_input))

        # Gmail smtp dispatcher
        elif "send email" in query or "send mail" in query:
            assistant.speak("What is the recipient's email address? Input in the terminal.")
            to_email = input("To: ").strip()
            assistant.speak("Specify the subject line.")
            subject = input("Subject: ").strip()
            assistant.speak("State the message body.")
            body = input("Body: ").strip()
            assistant.speak(features.send_email(subject, body, to_email))

        # Default handler
        else:
            if assistant.mode == "JARVIS":
                assistant.speak("I apologize, Sir. That command exceeds my current instructions.")
            else:
                assistant.speak("My apologies, Boss. I don't have a direct module designed for that command.")

if __name__ == "__main__":
    main()