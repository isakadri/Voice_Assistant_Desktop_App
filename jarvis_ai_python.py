import os
import sys
import time
import datetime
import webbrowser
import subprocess
import speech_recognition as sr
import pyttsx3
import pyautogui
import wikipedia
import wolframalpha
import requests
import re
from pygame import mixer
import json
import openai
import google.generativeai as genai
from dotenv import load_dotenv
import pytesseract
from PIL import Image, ImageGrab
import io
import numpy as np
import tkinter as tk
import math
import random
from tkinter import ttk, scrolledtext

# Initialize the text-to-speech engine
name = None
usr = ""
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female voice
engine.setProperty('rate', 180)  # Speed of speech

# Configuration
WAKE_WORD = "wake up fredrisk"  # Change this to your preferred wake word
PASS_PHRASE = "my voice is my password"
API_KEYS = {
    'wolframalpha': '8G9JVE-35RT6KEHWA',
    'openai': 'AIzaSyBXKUprA6rq4n1oTaPfACVEkH0cCm4tkfA', # Optional
    'serpapi': '30a311bf9cea8b27b118a9372b654a0c0a779423fb50fe0f35fb758deef884e6'  # SERPAPI key
}
GEMINI_API_KEY = "AIzaSyBQvbKcks4-FxuH4NUNt7oNKsHzOUkUreM"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')
gemini_chat = gemini_model.start_chat(history=[])

# Configure Tesseract OCR path (update this to your Tesseract installation path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize APIs (optional)
try:
    wolfram_client = wolframalpha.Client(API_KEYS['wolframalpha'])
except:
    wolfram_client = None

try:
    openai.api_key = API_KEYS['openai']
except:
    pass

class ScreenAssistant:
    def __init__(self):
        pyautogui.FAILSAFE = True  # Enable failsafe

    def take_screenshot(self, save_path=None, region=None):
        """Take a screenshot and save it to the specified path"""
        if save_path is None:
            screenshots_dir = "C:\\Screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            save_path = os.path.join(screenshots_dir, f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png")
        
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return save_path

    def get_screen_info(self):
        """Get information about the screen"""
        width, height = pyautogui.size()
        current_x, current_y = pyautogui.position()
        
        info = (
            f"Screen Resolution: {width}x{height}\n"
            f"Current Mouse Position: ({current_x}, {current_y})\n"
        )
        return info

    def move_mouse(self, x, y, duration=1):
        """Move mouse to specified coordinates"""
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, x=None, y=None, button='left'):
        """Click at specified coordinates or current position"""
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)

    def type_text(self, text, interval=0.1):
        """Type the specified text"""
        pyautogui.typewrite(text, interval=interval)
    
    def read_screen_text(self, region=None):
        """
        Read text from the screen using OCR
        :param region: Tuple (x, y, width, height) defining region to capture. If None, captures full screen.
        :return: Extracted text
        """
        try:
            # Take screenshot of specified region or full screen
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to PIL Image for OCR processing
            img = screenshot.convert('L')  # Convert to grayscale for better OCR
            
            # Use Tesseract to do OCR on the image
            text = pytesseract.image_to_string(img)
            
            # Clean up the text
            text = ' '.join(text.split())  # Remove excessive whitespace
            return text if text.strip() else "No readable text found on screen."
            
        except Exception as e:
            print(f"Error in read_screen_text: {e}")
            return f"Sorry, I couldn't read the screen. Error: {str(e)}"

    def select_region_interactively(self):
        """
        Guide user to select a screen region for reading
        :return: Tuple (x, y, width, height) or None if cancelled
        """
        try:
            speak("Please move your mouse to the top-left corner of the area you want to read, then say 'mark'")
            top_left = None
            bottom_right = None
            
            # Get top-left corner
            while True:
                query = take_command().lower()
                if 'mark' in query:
                    top_left = pyautogui.position()
                    speak(f"Top-left corner marked at {top_left}. Now move to the bottom-right corner and say 'mark' again")
                    break
                elif 'cancel' in query:
                    speak("Region selection cancelled")
                    return None
            
            # Get bottom-right corner
            while True:
                query = take_command().lower()
                if 'mark' in query:
                    bottom_right = pyautogui.position()
                    break
                elif 'cancel' in query:
                    speak("Region selection cancelled")
                    return None
            
            # Calculate region
            x = min(top_left[0], bottom_right[0])
            y = min(top_left[1], bottom_right[1])
            width = abs(bottom_right[0] - top_left[0])
            height = abs(bottom_right[1] - top_left[1])
            
            speak(f"Region selected: {width} pixels wide and {height} pixels tall. Say 'confirm' to proceed or 'cancel' to start over")
            
            # Final confirmation
            query = take_command().lower()
            if 'confirm' in query:
                return (x, y, width, height)
            else:
                return self.select_region_interactively()
                
        except Exception as e:
            print(f"Error in select_region_interactively: {e}")
            speak("Sorry, I encountered an error while selecting the region")
            return None

# Initialize the screen assistant
screen_assistant = ScreenAssistant()

# Morphing Circle Interface
class AIAssistantInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Fredrisk AI Assistant with Morphing Circle")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Create main frames
        self.sidebar = tk.Frame(root, width=200, bg='#34495e')
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        self.main_area = tk.Frame(root, bg='#2c3e50')
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create circle canvas
        self.canvas = tk.Canvas(self.main_area, width=400, height=400, bg='#2c3e50', highlightthickness=0)
        self.canvas.pack(pady=20)
        
        # Create chat area
        self.chat_frame = tk.Frame(self.main_area, bg='#2c3e50')
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_log = scrolledtext.ScrolledText(
            self.chat_frame, 
            width=60, 
            height=10, 
            bg='#ecf0f1', 
            fg='#2c3e50',
            font=('Arial', 10)
        )
        self.chat_log.pack(padx=10, pady=10)
        self.chat_log.insert(tk.END, "Fredrisk AI: Hello! How can I help you today?\n")
        self.chat_log.config(state=tk.DISABLED)
        
        # Input area
        self.input_frame = tk.Frame(self.chat_frame, bg='#2c3e50')
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.user_input = ttk.Entry(self.input_frame, font=('Arial', 12))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind('<Return>', self.send_message)
        
        self.send_btn = ttk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)
        
        # Sidebar controls
        ttk.Label(self.sidebar, text="Fredrisk AI", background='#34495e', foreground='white', 
                 font=('Arial', 14, 'bold')).pack(pady=20)
        
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.sidebar, text="Animation Speed", background='#34495e', foreground='white').pack(pady=5)
        self.speed_scale = ttk.Scale(self.sidebar, from_=1, to=20, orient=tk.HORIZONTAL)
        self.speed_scale.set(10)
        self.speed_scale.pack(padx=10, pady=5)
        
        ttk.Label(self.sidebar, text="Morphing Intensity", background='#34495e', foreground='white').pack(pady=5)
        self.intensity_scale = ttk.Scale(self.sidebar, from_=1, to=30, orient=tk.HORIZONTAL)
        self.intensity_scale.set(15)
        self.intensity_scale.pack(padx=10, pady=5)
        
        ttk.Button(self.sidebar, text="Change Color Theme", command=self.change_theme).pack(pady=20)
        ttk.Button(self.sidebar, text="Reset", command=self.reset).pack(pady=10)
        
        # Circle properties
        self.center_x = 200
        self.center_y = 200
        self.base_radius = 100
        self.points = 20
        self.angles = [2 * math.pi * i / self.points for i in range(self.points)]
        self.offsets = [0] * self.points
        self.colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
        self.current_color = random.choice(self.colors)
        
        # Start animation
        self.morph_circle()
    
    def morph_circle(self):
        self.canvas.delete("circle")
        
        speed = self.speed_scale.get() / 100
        intensity = self.intensity_scale.get() / 5
        
        # Update offsets for morphing effect
        for i in range(self.points):
            self.offsets[i] += random.uniform(-speed, speed)
            # Keep offsets within bounds
            self.offsets[i] = max(-intensity, min(intensity, self.offsets[i]))
        
        # Draw the morphing circle
        points = []
        for i in range(self.points):
            radius = self.base_radius + self.offsets[i] * 10
            x = self.center_x + radius * math.cos(self.angles[i])
            y = self.center_y + radius * math.sin(self.angles[i])
            points.append(x)
            points.append(y)
        
        # Create the polygon
        self.canvas.create_polygon(
            points, 
            fill=self.current_color, 
            outline='white', 
            width=2, 
            smooth=True,
            tags="circle"
        )
        
        # Add some glow effect
        for i in range(3):
            self.canvas.create_oval(
                self.center_x - self.base_radius - i*5,
                self.center_y - self.base_radius - i*5,
                self.center_x + self.base_radius + i*5,
                self.center_y + self.base_radius + i*5,
                outline=self.current_color,
                width=1,
                tags="circle"
            )
        
        # Schedule next update
        self.root.after(50, self.morph_circle)
    
    def change_theme(self):
        self.current_color = random.choice(self.colors)
        self.canvas.configure(bg=random.choice(['#2c3e50', '#1a1a2e', '#16213e', '#0f3460']))
    
    def reset(self):
        self.offsets = [0] * self.points
        self.current_color = random.choice(self.colors)
        self.canvas.configure(bg='#2c3e50')
        self.speed_scale.set(10)
        self.intensity_scale.set(15)
    
    def send_message(self, event=None):
        message = self.user_input.get()
        if message.strip():
            self.chat_log.config(state=tk.NORMAL)
            self.chat_log.insert(tk.END, f"You: {message}\n")
            
            # Simple AI responses
            responses = [
                "I'm analyzing your request...",
                "That's an interesting question!",
                "Let me think about that for a moment.",
                "I'm processing your input now.",
                "Thank you for your message. How can I assist further?",
                "I'm here to help with any questions you might have.",
                "That's a great point! Let me provide more information."
            ]
            
            self.chat_log.insert(tk.END, f"Fredrisk AI: {random.choice(responses)}\n")
            self.chat_log.see(tk.END)
            self.chat_log.config(state=tk.DISABLED)
            
            self.user_input.delete(0, tk.END)

def speak(audio):
    """Convert text to speech"""
    print(f"Fredrisk: {audio}")
    engine.say(audio)
    engine.runAndWait()

def voice_authentication():
    """Authenticate user by voice"""
    speak("Voice authentication required. Please say the password.")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Listen for passphrase
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print("Listening for password...")
                r.adjust_for_ambient_noise(source)
                audio = r.listen(source, timeout=5)
            
            # Recognize passphrase
            try:
                print("Verifying passwords...")
                spoken_phrase = r.recognize_google(audio, language='en-in').lower()
                print(f"User said: {spoken_phrase}")
                
                if PASS_PHRASE.lower() in spoken_phrase:
                    speak("Voice authentication successful. Welcome back!")
                    return True
                else:
                    remaining_attempts = max_attempts - (attempt + 1)
                    if remaining_attempts > 0:
                        speak(f"Authentication failed. {remaining_attempts} attempts remaining.")
                    else:
                        speak("Maximum attempts reached. Exiting.")
                        return False
                        
            except sr.UnknownValueError:
                speak("Could not understand audio. Please try again.")
            except sr.RequestError as e:
                speak(f"Could not request results; {e}")
                
        except Exception as e:
            print(f"Authentication error: {e}")
            speak("An error occurred during authentication. Please try again.")
    
    return False

def wish_me():
    """Greet the user based on time of day"""
    hour = datetime.datetime.now().hour
    speak("I am Fredrisk. Let me know your name please")
    stu = take_command()
    global name
    name = str(stu)
    if name == "none":
        name = "User"  # Default name if not provided
    
    if 0 <= hour < 12:
        speak(f"Good Morning {name}. I am Fredrisk. How may I assist you today?")
    elif 12 <= hour < 18:
        speak(f"Good Afternoon {name}. I am Fredrisk. How may I assist you today?")
    else:
        speak(f"Good Evening {name}. I am Fredrisk. How may I assist you today?")

def hello():
    speak(f"Hello {name}! I am Fredrisk, your personal assistant. How are you today? How can I help you?")   

def chat_with_gemini(query):
    """Chat with Gemini AI model with conversation history"""
    try:
        response = gemini_chat.send_message(query)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        return None

def start_jarvis():
    query = "activate jarvis mode"
    """Chat with Gemini AI model with conversation history"""
    try:
        response = gemini_chat.send_message(query)
        print(response)
        return response.text
        
    except Exception as e:
        print(f"Gemini Error: {str(e)}")
        return None    

def take_command():
    """Take microphone input from user and return as text"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query.lower()
    except Exception as e:
        print("Say that again please...")
        return "None"

def read_screen(region=None):
    """
    Read text from screen and speak it
    :param region: Tuple (x, y, width, height) defining region to read. If None, reads full screen.
    """
    try:
        speak("Reading screen content, please wait...")
        
        # If no region specified, ask user if they want to select a specific area
        if region is None:
            speak("Would you like me to read the entire screen or a specific region? Say 'full screen' or 'select region'")
            choice = take_command().lower()
            
            if 'select' in choice or 'region' in choice:
                region = screen_assistant.select_region_interactively()
                if region is None:
                    return
        
        # Read the text
        text = screen_assistant.read_screen_text(region)
        
        # Speak the text in chunks if it's long
        if len(text) > 500:
            speak("There's a lot of text. I'll read it in parts.")
            chunks = [text[i:i+500] for i in range(0, len(text), 500)]
            for chunk in chunks:
                speak(chunk)
                time.sleep(0.5)
        else:
            speak(text)
            
    except Exception as e:
        speak(f"Sorry, I couldn't read the screen. Error: {str(e)}")

def perform_web_search(query):
    """Perform web search"""
    speak("What would you like me to search for?")
    search_query = take_command()
    if search_query != "none":
        url = f"https://www.google.com/search?q={search_query}"
        webbrowser.open(url)
        speak(f"Here are the search results for {search_query}")
    else:
        speak("I didn't catch that. Please try again.")

def get_wikipedia_summary(query):
    """Get summary from Wikipedia"""
    speak("Searching Wikipedia...")
    query = query.replace("wikipedia", "")
    try:
        results = wikipedia.summary(query, sentences=2)
        speak("According to Wikipedia")
        speak(results)
    except:
        speak("No results found on Wikipedia.")

def type_program():
    """Get code from Gemini and type it on screen"""
    speak("What kind of program would you like me to type? Please describe it.")
    program_description = take_command()
    
    if program_description == "none":
        speak("I didn't understand your request. Please try again.")
        return
    
    # Get code from Gemini
    speak("Generating the program, please wait...")
    prompt = f"Please provide a complete Python program for: {program_description}. Include only the code with no additional explanations or markdown formatting."
    
    try:
        response = gemini_chat.send_message(prompt)
        code = response.text
        
        # Clean up the response (remove markdown code blocks if present)
        if '```python' in code:
            code = code.split('```python')[1].split('```')[0]
        elif '```' in code:
            code = code.split('```')[1].split('```')[0]
        
        speak("I'll start typing the program in 5 seconds. Please focus on the text input area where you want the code.")
        time.sleep(5)
        
        # Type the code
        pyautogui.PAUSE = 0.05  # Delay between each keypress
        lines = code.split('\n')
        for line in lines:
            pyautogui.typewrite(line)
            pyautogui.press('enter')
            time.sleep(0.1)
            
        speak("Finished typing the program.")
        
    except Exception as e:
        print(f"Error in type_program: {e}")
        speak("Sorry, I couldn't generate or type the program. Please try again.")

def get_wolframalpha_answer(query):
    """Get answer from WolframAlpha"""
    if wolfram_client:
        try:
            res = wolfram_client.query(query)
            answer = next(res.results).text
            speak("According to WolframAlpha")
            speak(answer)
        except:
            speak("Sorry, I couldn't find an answer for that.")
    else:
        speak("WolframAlpha API is not configured.")
        
def sameer():
    speak("That's not appropriate language.")

def play_music():
    """Play music from a specific directory"""
    music_dir = 'C://Users//ram//Music'  # Change to your music directory
    songs = os.listdir(music_dir)
    if songs:
        speak("Playing music")
        os.startfile(os.path.join(music_dir, songs[0]))
    else:
        speak("No music files found in the directory.")

def get_current_time():
    """Speak the current time"""
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    speak(f"The current time is {current_time}")

def get_current_date():
    """Speak the current date"""
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {current_date}")

def take_screenshot():
    """Take a screenshot"""
    try:
        path = screen_assistant.take_screenshot()
        speak(f"Screenshot saved to {path}")
    except Exception as e:
        speak(f"Sorry, I couldn't take the screenshot. Error: {str(e)}")

def shutdown_computer():
    """Shutdown the computer"""
    speak("Are you sure you want to shutdown the computer? Say shutdown or no")
    confirmation = take_command()
    if 'shutdown' in confirmation:
        speak("Shutting down the computer in 30 seconds")
        os.system("shutdown /s /t 30")
    else:
        speak("Shutdown cancelled")

def restart_computer():
    """Restart the computer"""
    speak("Are you sure you want to restart the computer? Say restart or no")
    confirmation = take_command()
    if 'restart' in confirmation:
        speak("Restarting the computer in 30 seconds")
        os.system("shutdown /r /t 30")
    else:
        speak("Restart cancelled")

def kkchutiya():
    speak("That's not appropriate language.")

def surajluly():
    speak("That's not appropriate language.")

def bhurebhai():
    speak("That's not appropriate language.")

def open_file(file_name):
    """Open a specific file"""
    file_paths = {
        'project file': r'C:\Projects\my_project.txt',
        'report': r'C:\Documents\report.docx',
        'presentation': r'C:\Documents\presentation.pptx'
    }
    
    if file_name in file_paths:
        try:
            speak(f"Opening {file_name}")
            os.startfile(file_paths[file_name])
        except Exception as e:
            speak(f"Sorry, I couldn't open the {file_name}. Please check the path.")
    else:
        speak("File not configured. Please add it to the file_paths dictionary.")

def set_reminder():
    """Set a reminder"""
    speak("What would you like to be reminded about?")
    reminder_text = take_command()
    speak("In how many minutes?")
    try:
        minutes = float(take_command())
        seconds = minutes * 60
        time.sleep(seconds)
        speak(f"Reminder: {reminder_text}")
    except:
        speak("Sorry, I didn't understand the time. Please try again.")

def thankyou():
    """Thank the user"""
    speak(f"Welcome {name} for using me. I hope I was able to help you. Have a great day ahead sir!")

def stop():
    """Stop the assistant"""
    speak("System exiting....")
    sys.exit()    

def get_weather(city=None):
    """Get weather information using OpenWeatherMap API"""
    if city is None:
        speak("Which city's weather would you like to know?")
        city = take_command()
        if city == "none":
            city = "your city"  # Default if no city specified
    
    try:
        api_key = "30d4741c779ba94c470ca1f63045390a"  # Your OpenWeatherMap API key
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric'  # For Celsius, use 'imperial' for Fahrenheit
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        
        # Extract weather information
        city_name = data['name']
        country = data['sys']['country']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_desc = data['weather'][0]['description'].title()
        
        # Format the weather report
        weather_report = (
            f"Weather in {city_name}, {country}:\n"
            f"Temperature: {temp}°C (Feels like {feels_like}°C)\n"
            f"Weather: {weather_desc}\n"
            f"Humidity: {humidity}%\n"
            f"Wind Speed: {wind_speed} m/s"
        )
        
        speak(weather_report)
        
    except requests.exceptions.RequestException as e:
        speak(f"Sorry, I couldn't fetch the weather data. Please check your internet connection.")
    except json.JSONDecodeError:
        speak("Sorry, there was an error processing the weather data.")
    except KeyError as e:
        speak("Sorry, I couldn't interpret the weather information properly.")
    except Exception as e:
        speak("Sorry, an unexpected error occurred while getting the weather.")

def send_email():
    """Send email (basic implementation)"""
    speak("This is a placeholder for email functionality")

def system_commands(command):
    """Execute system commands"""
    if 'lock' in command:
        speak("Locking the system")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif 'sleep' in command:
        speak("Putting the system to sleep")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif 'hibernate' in command:
        speak("Hibernating the system")
        os.system("shutdown /h")

def control_volume(action):
    """Control system volume"""
    if 'increase' in action:
        pyautogui.press('volumeup')
        speak("Volume increased")
    elif 'decrease' in action:
        pyautogui.press('volumedown')
        speak("Volume decreased")
    elif 'mute' in action:
        pyautogui.press('volumemute')
        speak("Sound muted")

def krushnakedarlul():
    speak("That's not appropriate language.")

def get_news():
    """Fetch news headlines"""
    try:
        api_key = "664e2dc3b4ba434ab5dd2d4279c8af12"  # Get from https://newsapi.org/
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "ok":
            articles = data["articles"][:5]  # Get top 5 headlines
            speak("Here are the top news headlines")
            for i, article in enumerate(articles, 1):
                speak(f"{i}. {article['title']}")
        else:
            speak("Sorry, couldn't fetch news at the moment")
    except:
        speak("Sorry, I couldn't retrieve the news")

def get_serpapi_answer(query):
    """Get detailed answer from SERPAPI (Google Search API)"""
    params = {
        'q': query,
        'api_key': API_KEYS['serpapi'],
        'hl': 'en',  # Language: English
        'gl': 'us',   # Country: US
        'num': 5      # Get more results for longer answers
    }
    
    try:
        response = requests.get('https://serpapi.com/search', params=params)
        data = response.json()
        answer_parts = []
        
        # 1. Check for featured snippet (answer box)
        if 'answer_box' in data:
            if 'answer' in data['answer_box']:
                answer_parts.append(data['answer_box']['answer'])
            if 'snippet' in data['answer_box']:
                answer_parts.append(data['answer_box']['snippet'])
            if 'snippet_highlighted_words' in data['answer_box']:
                answer_parts.extend(data['answer_box']['snippet_highlighted_words'])

        # 2. Check for knowledge graph
        if 'knowledge_graph' in data:
            if 'description' in data['knowledge_graph']:
                answer_parts.append(data['knowledge_graph']['description'])
            if 'description_source' in data['knowledge_graph']:
                answer_parts.append(f"Source: {data['knowledge_graph']['description_source']}")

        # 3. Get multiple organic results
        if 'organic_results' in data:
            for i, result in enumerate(data['organic_results'][:3]):  # Get top 3 results
                if 'snippet' in result:
                    answer_parts.append(f"\nFrom {result.get('source', 'a source')}:")
                    answer_parts.append(result['snippet'])
                if 'link' in result:
                    answer_parts.append(f"More info: {result['link']}")

        # 4. Check for "People also ask" section
        if 'related_questions' in data:
            answer_parts.append("\nRelated questions:")
            for question in data['related_questions'][:3]:  # Get top 3 related questions
                answer_parts.append(f"- {question['question']}")
                if 'snippet' in question:
                    answer_parts.append(f"  {question['snippet']}")

        # Format the final answer
        if answer_parts:
            full_answer = "\n".join(answer_parts)
            
            # Ensure the answer isn't too long for speech (limit to 500 chars)
            if len(full_answer) > 500:
                full_answer = full_answer[:497] + "..."
                
            return full_answer
        else:
            return None
    
    except Exception as e:
        print(f"SERPAPI Error: {str(e)}")
        return None

def open_application(app_name):
    """Open applications based on voice command"""
    app_paths = {
        'vs code': r'C:\Users\YourUsername\AppData\Local\Programs\Microsoft VS Code\Code.exe',
        'chrome': r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'word': 'WINWORD.EXE',
        'excel': 'EXCEL.EXE',
        'powerpoint': 'POWERPNT.EXE',
        'paint': 'mspaint.exe',
        'file explorer': 'explorer.exe',
        'command prompt': 'cmd.exe',
        'spotify': r'C:\Users\YourUsername\AppData\Roaming\Spotify\Spotify.exe',
        'whatsapp': r'C:\Users\ram\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Chrome Apps',
        'zoom': r'C:\Users\YourUsername\AppData\Roaming\Zoom\bin\Zoom.exe',
        'teams': r'C:\Users\YourUsername\AppData\Local\Microsoft\Teams\current\Teams.exe',
        'youtube': r'C:\Program Files\Google\Chrome\Application\chrome.exe --app=https://www.youtube.com',
    }
    
    if app_name in app_paths:
        try:
            speak(f"Opening {app_name}")
            subprocess.Popen(app_paths[app_name])
        except Exception as e:
            speak(f"Sorry, I couldn't open {app_name}. Please check the path.")
    else:
        speak("Application not configured. Please add it to the app_paths dictionary.")

def process_command(query):
    """Process user commands"""
    if 'wikipedia' in query:
        get_wikipedia_summary(query)
    elif 'open' in query:
        app_name = query.replace('open', '').strip()
        open_application(app_name)
    elif 'search' in query:
        perform_web_search(query)
    elif 'play music' in query:
        play_music()
    elif 'time' in query:
        get_current_time()
    elif 'date' in query:
        get_current_date()
    elif 'shutdown' in query:
        shutdown_computer()
    elif 'restart' in query:
        restart_computer()
    elif 'screenshot' in query:
        take_screenshot()
    elif 'set reminder' in query:
        set_reminder()
    elif 'screen info' in query:
        try:
            info = screen_assistant.get_screen_info()
            speak(info)
        except Exception as e:
            speak(f"Sorry, I couldn't get screen information. Error: {str(e)}")
    elif 'move mouse' in query:
        try:
            speak("Please say the X coordinate")
            x = int(take_command())
            speak("Please say the Y coordinate")
            y = int(take_command())
            screen_assistant.move_mouse(x, y)
            speak(f"Mouse moved to position {x}, {y}")
        except Exception as e:
            speak(f"Sorry, I couldn't move the mouse. Error: {str(e)}")
    elif 'click' in query:
        try:
            screen_assistant.click()
            speak("Mouse clicked at current position")
        except Exception as e:
            speak(f"Sorry, I couldn't perform the click. Error: {str(e)}")
    elif 'type' in query:
        try:
            text = query.replace('type', '').strip()
            if not text:
                speak("What would you like me to type?")
                text = take_command()
                
            screen_assistant.type_text(text)
            speak(f"Typed: {text}")
        except Exception as e:
            speak(f"Sorry, I couldn't type the text. Error: {str(e)}")
    elif 'weather' in query:
        speak("Please tell me the city name for which you want the weather information.")
        city = take_command()
        get_weather(city)
    elif 'send email' in query:
        send_email()
    elif 'lock' in query or 'sleep' in query or 'hibernate' in query:
        system_commands(query)
    elif 'volume' in query:
        control_volume(query)
    elif 'sameer' in query or 'samir' in query:
        sameer()
    elif 'type a program' in query or 'write a program' in query:
        type_program()
    elif 'news' in query:
        get_news()
    elif 'calculate' in query and wolfram_client:
        get_wolframalpha_answer(query)
    elif 'wish me' in query:
        wish_me()
    elif 'thank you' in query or 'thanks' in query or "thank" in query:
        thankyou()
    elif 'stop' in query or 'exit' in query:
        stop()
    elif 'hello' in query:
        hello()
    elif 'exit' in query or 'quit' in query or 'goodbye' in query:
        speak("Goodbye Sir. Have a nice day!")
        sys.exit()
    elif 'shut up' in query:
        speak(f"I am sorry {name}, I will not talk again")  
        sys.exit()
    elif 'read screen' in query or 'read the screen' in query or 'read text' in query:
        read_screen()
    elif 'kk' in query or 'k k ' in query or 'k k chutiya' in query or 'kk chutiya' in query:
        kkchutiya()
    elif 'bhure' in query or 'tomy' in query or 'pradeep' in query or 'bhhure' in query or 'bhur' in query:
        bhurebhai()
    elif 'show interface' in query or 'show visual' in query or 'show gui' in query:
        speak("Opening visual interface")
        root = tk.Tk()
        app = AIAssistantInterface(root)
        root.mainloop()
    else:
        # First try Gemini AI
        speak("Here is your answer sir...")
        gemini_response = chat_with_gemini(query)
        
        if gemini_response:
            # Process Gemini's response for speech
            if len(gemini_response) > 500:
                gemini_response = gemini_response[:497] + "..."
            cleaned = re.sub(r'[*\\{;:"()]', '', gemini_response)
            speak(cleaned)
        else:
            # If Gemini fails, try SERPAPI
            answer = get_serpapi_answer(query)
            if answer:
                speak("Let me look that up for you.")
                time.sleep(1)
                
                # Split long answers into chunks for better speech delivery
                max_chunk = 300  # Characters per speech chunk
                if len(answer) > max_chunk:
                    chunks = [answer[i:i+max_chunk] for i in range(0, len(answer), max_chunk)]
                    for chunk in chunks:
                        speak(chunk)
                        time.sleep(0.5)  # Small pause between chunks
                else:
                    cleaned = re.sub(r'[*\\{;:",.()]', '', answer)
                    speak(cleaned)
            else:
                speak("I'm sorry, I couldn't find information about that. Would you like me to try a web search?")

if __name__ == "__main__":
    # First perform voice authentication
    if voice_authentication():
        # Authentication successful, proceed with wish_me()
        start_jarvis()
        wish_me()
        
        while True:
            query = take_command().lower()
            
            if WAKE_WORD in query:
                speak("Welcome Sir! Nice to meet you again.")
                command = take_command().lower()
                process_command(command)
            elif 'none' not in query:
                process_command(query)
    else:
        speak("Authentication failed. Exiting the system.")
        sys.exit()