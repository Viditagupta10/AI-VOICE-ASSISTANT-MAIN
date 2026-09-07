import os
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
from urllib.parse import quote

# pip install pocketsphinx

recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapi = os.getenv("NEWS_API_KEY", "YOUR_NEWS_API_KEY")

def speak_old(text):
    engine.say(text)
    engine.runAndWait()

def speak(text):
    try:
        tts = gTTS(text)
        tts.save('temp.mp3')
        if not os.path.exists('temp.mp3'):
            raise RuntimeError("Google TTS did not create temp.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load('temp.mp3')
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as error:
        print(f"TTS error; {error}")
        speak_old(text)
    finally:
        if os.path.exists('temp.mp3'):
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
            except pygame.error:
                pass
            try:
                os.remove('temp.mp3')
            except PermissionError:
                print("TTS cleanup skipped because temp.mp3 is still in use")

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
    command = c.lower()
    if "youtube" in command and "search" in command:
        search_term = c[command.find("search") + len("search"):].strip()
        if search_term.lower().startswith("for "):
            search_term = search_term[4:].strip()
        if search_term.lower().endswith(" on youtube"):
            search_term = search_term[:-11].strip()
        webbrowser.open_new_tab(
            f"https://www.youtube.com/results?search_query={quote(search_term)}"
        )
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
        # Let OpenAI handle the request
        output = aiProcess(c)
        speak(output) 





if __name__ == "__main__":
    speak("Initializing Jarvis....")
    while True:
        # Listen for the wake word "Jarvis"
        # obtain audio from the microphone
        r = sr.Recognizer()
         
        print("recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=5, phrase_time_limit=3)
            word = r.recognize_google(audio)
            print(f"Heard: {word}")
            if "jarvis" in word.lower():
                speak("Ya")
                command = word[word.lower().find("jarvis") + len("jarvis"):].strip()
                if not command:
                    # Listen for a command when it was not included with the wake word.
                    with sr.Microphone() as source:
                        print("Jarvis Active...")
                        audio = r.listen(source, timeout=5, phrase_time_limit=20)
                        command = r.recognize_google(audio)
                print(f"Command: {command}")

                processCommand(command)


        except Exception as e:
            print("Error; {0}".format(e))



