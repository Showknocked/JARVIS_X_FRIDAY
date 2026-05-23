import os
import json
import smtplib
import datetime
import webbrowser
import urllib.parse
import difflib
import requests
import wikipedia
import psutil
import subprocess

def get_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}

config = get_config()
DICTIONARY_FILE = "dictionary_db.json"

# 1. Wikipedia Search Integration
def search_wikipedia(query):
    try:
        results = wikipedia.summary(query, sentences=2)
        return f"According to Wikipedia: {results}"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple definitions found: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        return "I could not locate matching wiki pages."
    except Exception:
        return "An issue occurred querying Wikipedia data."

# 2. Local/Web Dictionary with autocorrect spell sensing
def load_dictionary():
    if os.path.exists(DICTIONARY_FILE):
        with open(DICTIONARY_FILE, "r") as f:
            return json.load(f)
    return {
        "computer": "An electronic device for processing and storing data.",
        "programming": "The execution of structured source code modules.",
        "ai": "Simulation of human-like decision parameters inside processors."
    }

def search_dictionary(word):
    db = load_dictionary()
    word = word.lower().strip()
    if word in db:
        return f"The definition of {word} is: {db[word]}"
    
    # Check close spellings using difflib
    matches = difflib.get_close_matches(word, db.keys(), n=1, cutoff=0.6)
    if matches:
        closest = matches[0]
        return f"I couldn't find '{word}'. Did you mean '{closest}'? Definition: {db[closest]}"
    
    # Try dynamic online backup lookup
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            meaning = data[0]['meanings'][0]['definitions'][0]['definition']
            db[word] = meaning
            with open(DICTIONARY_FILE, "w") as f:
                json.dump(db, f, indent=4)
            return f"The definition of {word} is: {meaning}"
    except Exception:
        pass
        
    return f"Definition not found for '{word}'."

# 3. Secure Mail utility
def send_email(subject, body, to_email):
    sender = config.get("SENDER_EMAIL")
    password = config.get("SENDER_PASSWORD")
    if not sender or not password or "your_email" in sender:
        return "Please configure the email credentials inside your config.json configuration."
        
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender, to_email, message)
        return "Email successfully dispatched."
    except Exception as e:
        return f"Failed to send email: {e}"

# 4. News Headlines Utility
def fetch_news():
    api_key = config.get("NEWS_API_KEY")
    if not api_key or "YOUR_" in api_key:
        # Secure, credential-free fallback feed
        try:
            r = requests.get("https://saurav.tech/NewsAPI/top-headlines/category/technology/us.json", timeout=5)
            if r.status_code == 200:
                articles = r.json().get("articles", [])[:3]
                headlines = [art["title"] for art in articles]
                return "Latest technology news: " + " | ".join(headlines)
        except Exception:
            pass
        return "Configure your NewsAPI Key in config.json to load global news modules."
        
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            articles = r.json().get("articles", [])[:3]
            headlines = [a["title"] for a in articles]
            return "Current major headlines: " + " ... ".join(headlines)
        return "Could not retrieve articles from the service."
    except Exception:
        return "Could not establish news server connections."

# 5. Todo manager
def manage_todo(action, item=""):
    todo_path = config.get("TODO_FILE", "todo.txt")
    if action == "add":
        if not item:
            return "Please define what task is being tracked."
        with open(todo_path, "a") as f:
            f.write(f"{item}\n")
        return f"Registered task: '{item}'."
        
    elif action == "read":
        if not os.path.exists(todo_path) or os.path.getsize(todo_path) == 0:
            return "Your pending task list is currently empty."
        with open(todo_path, "r") as f:
            tasks = f.readlines()
        task_str = "".join([f"Task {i+1}: {task}" for i, task in enumerate(tasks)])
        return f"Your active tasks are:\n{task_str}"
        
    elif action == "clear":
        if os.path.exists(todo_path):
            os.remove(todo_path)
        return "Task list cleared successfully."

# 6. Web and Custom Search Engine
def open_website(site_name):
    sites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "github": "https://www.github.com",
        "stackoverflow": "https://stackoverflow.com",
        "reddit": "https://www.reddit.com"
    }
    site_name = site_name.lower().strip()
    if site_name in sites:
        webbrowser.open(sites[site_name])
        return f"Opening {site_name}."
    else:
        url = f"https://www.google.com/search?q={urllib.parse.quote(site_name)}"
        webbrowser.open(url)
        return f"Searching query '{site_name}' via Google."

# 7. Weather Module (No API Key Required Fallback)
def fetch_weather(city=""):
    if not city:
        try:
            geo_req = requests.get("https://ipapi.co/json/", timeout=4)
            if geo_req.status_code == 200:
                city = geo_req.json().get("city", "New York")
        except Exception:
            city = "New York"

    api_key = config.get("WEATHER_API_KEY")
    if not api_key or "YOUR_" in api_key:
        try:
            url = f"https://wttr.in/{city}?format=1"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return f"Weather details for {r.text.strip()}"
        except Exception:
            pass
        return "Please define OpenWeatherMap variables inside your config.json configuration."

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            desc = data["weather"][0]["description"]
            speed = data["wind"]["speed"]
            return f"The current forecast for {city} features {desc}. The temp is {temp}°C, humidity is {humidity}%, and wind speeds are {speed} meters per second."
        return f"Unable to fetch weather reports for '{city}'."
    except Exception:
        return "The weather service is offline."

# 8. Geo-Coordinates lookup
def get_current_location():
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            city = data.get("city")
            region = data.get("region")
            lat = data.get("latitude")
            lon = data.get("longitude")
            return f"Coordinates located at {city}, {region}. Latitude: {lat}, Longitude: {lon}."
    except Exception:
        pass
    return "Failed to establish current geolocation data."

# 9. Video Downloader via yt-dlp
def download_youtube_video(video_url):
    if not video_url:
        return "Please clarify the URL of your media file."
    try:
        target_dir = os.path.expanduser("~/Downloads")
        cmd = ["yt-dlp", "-P", target_dir, video_url]
        subprocess.run(cmd, check=True)
        return "Download successfully routed and exported to your Downloads folder."
    except Exception as e:
        return f"Unable to process download request: {e}"

# 10. Native macOS Core Integrations
def adjust_system_volume(level):
    try:
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"], check=True)
        return f"System volume altered to {level} percent."
    except Exception:
        return "Unable to access core macOS volume settings."

def get_system_diagnostics():
    try:
        cpu = psutil.cpu_percent()
        battery = psutil.sensors_battery()
        bat_pct = battery.percent if battery else "Unavailable"
        is_charging = battery.power_plugged if battery else False
        charging_status = "charging" if is_charging else "draining"
        return f"Host parameters check: CPU load is at {cpu}%. Battery is at {bat_pct}% and currently {charging_status}."
    except Exception:
        return "An failure occurred parsing hardware parameters."

def get_date_time():
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %B %d, %Y")
    return f"Today is {date_str}, and it is currently {time_str}."
