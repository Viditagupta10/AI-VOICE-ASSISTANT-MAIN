import os
import subprocess
import ctypes
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
from urllib.parse import quote

os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:
    import pygame
except ImportError:
    pygame = None

def load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = [part.strip() for part in line.split("=", 1)]
            if key and key not in os.environ:
                os.environ[key] = value.strip('"').strip("'")


load_env_file()

# pip install pocketsphinx

recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapi = os.getenv("NEWS_API_KEY", "YOUR_NEWS_API_KEY")

def acquire_single_instance():
    if os.name != "nt":
        return True

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int

    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, False, "Local\\JarvisVoiceAssistant")
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == 183:
        kernel32.CloseHandle(handle)
        return None
    return handle

def speak_old(text):
    try:
        engine.stop()
    except Exception:
        pass
    engine.say(text)
    engine.runAndWait()

def speak(text):
    text = str(text).strip()
    if not text:
        return

    audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp.mp3")
    try:
        if pygame is None:
            raise RuntimeError("pygame is not installed")

        gTTS(text=text, lang="en").save(audio_path)
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as error:
        print(f"Online speech playback failed; using Windows speech: {error}")
        speak_old(text)
    finally:
        if pygame is not None:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass
        try:
            os.remove(audio_path)
        except FileNotFoundError:
            pass
        except PermissionError:
            print("Speech audio cleanup skipped because the file is still in use")

def aiProcess(command):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"))

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a virtual assistant named jarvis skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
        {"role": "user", "content": command}
    ]
    )

    return completion.choices[0].message.content

def processCommand(c):
    command = c.lower().strip(" \t\r\n,!.?")
    if not command:
        return

    if "how are you" in command:
        speak("I am doing well, thank you for asking. How can I help you today?")
        return
    if any(greeting in command.split() for greeting in ("hello", "hi", "hey")):
        speak("Hello! I am Jarvis, your voice assistant. How can I help you?")
        return
    if "what is your name" in command or "who are you" in command:
        speak("I am Jarvis, your virtual assistant.")
        return
    if "good morning" in command:
        speak("Good morning! I hope your day goes wonderfully.")
        return
    if "good night" in command:
        speak("Good night. Sleep well and have sweet dreams.")
        return
    if "thank you" in command:
        speak("You are welcome. I am here to help.")
        return
    if "youtube" in command and "search" in command:
        search_term = c[command.find("search") + len("search"):].strip()
        if search_term.lower().startswith("for "):
            search_term = search_term[4:].strip()
        if search_term.lower().endswith(" on youtube"):
            search_term = search_term[:-11].strip()
        webbrowser.open_new_tab(
            f"https://www.youtube.com/results?search_query={quote(search_term)}"
        )
    elif "google" in command and "search" in command:
        search_term = c[command.find("search") + len("search"):].strip(" ,.!?")
        if search_term.lower().startswith("for "):
            search_term = search_term[4:].strip()
        for suffix in (" on google", " in google", " using google"):
            if search_term.lower().endswith(suffix):
                search_term = search_term[:-len(suffix)].strip()
                break
        if search_term:
            webbrowser.open_new_tab(
                f"https://www.google.com/search?q={quote(search_term)}"
            )
        else:
            speak("What would you like me to search for on Google?")
    elif "open google" in command:
        webbrowser.open("https://google.com")
    elif "open facebook" in command:
        webbrowser.open("https://facebook.com")
    elif "open youtube" in command:
        webbrowser.open("https://youtube.com")
    elif "open linkedin" in command:
        webbrowser.open("https://linkedin.com")
    elif command.startswith("play"):
        song = command.split(" ")[1]
        link = musicLibrary.music[song]
        webbrowser.open(link)

    elif "news" in command:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}")
        if r.status_code == 200:
            # Parse the JSON response
            data = r.json()
            
            # Extract the articles
            articles = data.get('articles', [])
            
            # Print the headlines
            for article in articles:
                speak(article['title'])

    else:
        try:
            output = aiProcess(c)
            speak(output or "I did not get a response. Please try again.")
        except Exception as error:
            print(f"AI response error: {error}")
            speak("I cannot answer that right now. Check the OpenAI API key and your internet connection.")





if __name__ == "__main__":
    instance_handle = acquire_single_instance()
    if instance_handle is None:
        print("Jarvis is already running. Close the other instance before starting another.")
        raise SystemExit(0)

    speak("Initializing Jarvis....")
    while True:
        r = sr.Recognizer()

        print("recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=5, phrase_time_limit=6)
            word = r.recognize_google(audio)
            print(f"Heard: {word}")

            if "jarvis" in word.lower():
                command = word[word.lower().find("jarvis") + len("jarvis"):].strip()

                if not command:
                    with sr.Microphone() as source:
                        print("Wake word detected. Listening for command...")
                        audio = r.listen(source, timeout=8, phrase_time_limit=20)
                        command = r.recognize_google(audio)

                if command:
                    command = command.strip().strip(",.!? ")

                if not command:
                    speak("I did not catch your command. Please try again.")
                    continue

                print(f"Command: {command}")
                processCommand(command)

        except Exception as e:
            print("Error; {0}".format(e))



