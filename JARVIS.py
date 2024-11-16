import speech_recognition as sr
import pyttsx3
import wikipediaapi
import webbrowser
import datetime
import os
import json
import requests
import threading
import random
from gtts import gTTS
import tempfile

# Initialize the recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Set TTS properties
engine.setProperty("rate", 150)
engine.setProperty("volume", 0.9)

# Save memory persistently


def save_memory():
    with open("memory.json", "w") as file:
        json.dump(memory, file)

# Load memory on startup


def load_memory():
    global memory
    try:
        with open("memory.json", "r") as file:
            content = file.read().strip()
            memory = json.loads(content) if content else {}
    except (FileNotFoundError, json.JSONDecodeError):
        memory = {}


# Memory dictionary
memory = {}

# Load application mapping from JSON file


def load_app_mapping():
    try:
        with open('app_mapping.json', 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading app mapping: {e}")
        return {}


# Load the app mapping into a variable
app_mapping = load_app_mapping()

# Voice response function that supports Hindi and Hinglish


def speak(text, language='en'):
    if any(char in text for char in "अआइईउऊऌएओ"):  # Check for Hindi characters
        tts = gTTS(text=text, lang='hi')
        with tempfile.NamedTemporaryFile(delete=True) as f:
            tts.save(f.name + '.mp3')
            os.system(f'start {f.name}.mp3')  # Play the Hindi audio file
    else:
        engine.say(text)
        engine.runAndWait()

# Function to handle commands


# Function to handle commands
def handle_command(command):
    if "hello" in command:
        speak("Hello, I am JARVIS. How can I assist you today?")
    elif "my name is" in command:
        name = command.replace("my name is", "").strip()
        memory["name"] = name
        speak(f"Nice to meet you, {name}!")
    elif "what is my name" in command:
        name = memory.get("name", "I don't know your name yet.")
        speak(f"Your name is {name}.")
    elif "time" in command:
        current_time = datetime.datetime.now().strftime("%H:%M")
        speak(f"The current time is {current_time}")
    elif "date" in command:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        speak(f"Today’s date is {current_date}")
    elif "weather" in command:
        api_key = "8df2794fcab292e33b7f615e59cad51b"  # You need to replace this with a real API key
        city = command.replace("weather in", "").strip()
        weather = get_weather(city, api_key)
        if weather:
            speak(f"The weather in {city} is currently {weather['description']} with a temperature of {weather['temp']}°C.")
        else:
            speak("I'm sorry, I couldn't get the weather information.")
    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        speak("Opening Google")
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube")
    elif "search wikipedia" in command or "about" in command:
        search_wikipedia(command)
    elif "play" in command and ("song" in command or "video" in command):
        play_youtube(command)
    elif "exit" in command or "stop" in command:
        speak("Goodbye! Sir.")
        save_memory()  # Save memory data before exiting
        exit()
    elif "open" in command:
        if "website" in command or "browser" in command:
            open_website(command)
        else:
            open_application(command)
    elif "tell me a fact" in command:
        facts = [
            "Did you know that honey never spoils?",
            "Bananas are berries, but strawberries aren't.",
            "A day on Venus is longer than a year on Venus.",
            "Octopuses have three hearts!",
            "Cows have best friends and get stressed when they are separated."
        ]
        fact = random.choice(facts)
        speak(fact)
    elif "remember" in command:
        if "favorite website" in command:
            website = command.replace(
                "remember my favorite website as", "").strip()
            memory["favorite_website"] = website
            speak(f"I'll remember your favorite website as {website}.")
    elif "favorite application" in command:
        app = command.replace(
            "remember my favorite application as", "").strip()
        memory["favorite_app"] = app
        speak(f"I'll remember your favorite application as {app}.")
    elif "favorite website" in command:
        website = memory.get("favorite_website", None)
        if website:
            webbrowser.open(f"https://{website}")
            speak(f"Opening your favorite website, {website}.")
        else:
            speak("I don't know your favorite website yet. You can tell me by saying, 'Remember my favorite website as...'")
    else:
        speak("Sorry, I didn't catch that. Please try again.")


# Function to open applications


def open_application(command):
    # Check if the command includes an application name
    for app_name, app_path in app_mapping.items():
        if app_name in command:
            try:
                os.startfile(app_path)  # Open the application
                speak(f"Opening {app_name}.")
                return
            except Exception as e:
                print(f"Error opening {app_name}: {e}")
                return
    # Provide feedback if no application is found
    speak("Sorry, I could not find that application.")

# Function to open websites


def open_website(command):
    # Extract the website name from the command
    website_name = command.replace("open ", "").strip()
    if "on browser" in website_name:
        website_name = website_name.replace("on browser", "").strip()

    # Replace spaces with '.' for subdomains
    website_name = website_name.replace(" ", ".")

    # List of common domain suffixes to try
    common_domains = ['.com', '.org', '.net',
                      '.edu', '.gov', '.co.in', '.io', '.me']

    # Attempt to find the best URL
    found_url = False
    for domain in common_domains:
        test_url = f"https://{website_name}{domain}"
        try:
            # Perform a request to see if the URL is valid
            response = requests.head(test_url, allow_redirects=True)
            if response.status_code == 200:
                webbrowser.open(test_url)  # Open the valid website
                speak(f"Opening {test_url}.")
                found_url = True
                break
        except requests.RequestException:
            continue  # Move on to the next domain if the request fails

    if not found_url:
        # If no valid URL was found, search on Google
        search_url = f"https://www.google.com/search?q={website_name}"
        webbrowser.open(search_url)
        speak(f"Could not find a specific website. Searching for {
              website_name} on Google.")

# Wikipedia search function


def search_wikipedia(command):
    # Specify a user agent
    wiki = wikipediaapi.Wikipedia(
        language="en",
        extract_format=wikipediaapi.ExtractFormat.WIKI,
        user_agent="JARVIS Voice Assistant (https://yourwebsite.com)"
    )

    topic = command.replace("search wikipedia for", "").strip()
    page = wiki.page(topic)

    if page.exists():
        summary = page.summary[:200]
        speak(f"According to Wikipedia, {summary}")
    else:
        speak("Sorry, I could not find information on that topic.")

# Function to play a specific video or song on YouTube


def play_youtube(command):
    search_query = command.replace("play", "").strip()
    if search_query:
        url = f"https://www.youtube.com/results?search_query={search_query}"
        webbrowser.open(url)
        speak(f"Playing {search_query} on YouTube.")
    else:
        speak("Please specify what you want to play.")

# Function to listen and recognize voice commands


def listen():
    with sr.Microphone() as source:
        print("Listening for command...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        command = None

        try:
            command = recognizer.recognize_google(
                audio, language='en-IN').lower()
            print(f"User said: {command}")
        except sr.UnknownValueError:
            pass  # Skip if the speech is not recognized
        except sr.RequestError as e:
            print(
                f"Could not request results from Google Speech Recognition service; {e}")

    return command  # Return the command (could be None)

def get_weather(city, api_key):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data["cod"] == 200:
            main = data["main"]
            weather = data["weather"][0]
            return {"temp": main["temp"], "description": weather["description"]}
        else:
            return None
    except Exception as e:
        print(f"Error getting weather: {e}")
        return None


def engage_conversation():
    speak("Let's have a chat. How are you feeling today?")

    while True:
        command = listen()
        if command:
            if "good" in command or "fine" in command:
                speak("That's great to hear! What made your day good?")
                follow_up_question("good")
            elif "bad" in command or "not well" in command:
                speak("I'm sorry to hear that. What seems to be bothering you?")
                follow_up_question("bad")
            elif "help" in command:
                speak("I’m here for you. What do you need help with?")
            elif "exit" in command or "stop" in command:
                speak("Goodbye! I'm always here for you.")
                break
            elif "search" in command:
                search_wikipedia(command)
            else:
                handle_command(command)


def follow_up_question(emotion):
    if emotion == "good":
        questions = [
            "What did you do today?",
            "Do you have any plans for the weekend?",
            "What’s something that made you smile?"
        ]
    else:
        questions = [
            "What’s been troubling you lately?",
            "Is there something specific you'd like to talk about?",
            "Would you like to hear a joke or something uplifting?"
        ]

    question = random.choice(questions)
    speak(question)

# Main loop for the assistant


def main():
    load_memory()  # Load memory data when the program starts
    speak("JARVIS activated. Listening for commands.")
    while True:
        command = listen()
        if command:
            if "chat" in command or "talk" in command:
                engage_conversation()
            else:
                handle_command(command)


# Run the assistant
if __name__ == "__main__":
    main()
