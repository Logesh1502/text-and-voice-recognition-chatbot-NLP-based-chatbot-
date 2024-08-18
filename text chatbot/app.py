from flask import Flask, render_template, request, jsonify
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import sounddevice as sd
import numpy as np
import wave
import speech_recognition as sr
import os

app = Flask(__name__)

# Initialize chatbots with different datasets
traffic_bot = ChatBot('TrafficBot')
general_bot = ChatBot('GeneralBot')

trainer1 = ListTrainer(traffic_bot)
trainer2 = ListTrainer(general_bot)

# Dataset 1: Traffic fines and rules
trainer1.train([
    'What is the penalty for driving without a valid license in India?',
    'Driving without a valid license in India can result in a fine of up to Rs. 5,000 and/or imprisonment of up to 3 months for the first offense.',
    'How much is the fine for overspeeding in India?',
    'The fine for overspeeding in India varies based on the vehicle type and speed limit violation. Generally, fines can range from Rs. 400 to Rs. 2,000.',
    'What are the consequences of driving under the influence of alcohol in India?',
    'Driving under the influence of alcohol in India can lead to a fine of up to Rs. 10,000 and/or imprisonment of up to 6 months for the first offense, along with license suspension.',
])

# Dataset 2: General knowledge
trainer2.train([
     "What is the maximum speed limit in urban areas in India?", 
     "The maximum speed limit in urban areas in India is generally 50 km/h, but it can vary based on specific road conditions and local regulations.",
    "Is it mandatory to wear a helmet while riding a two-wheeler in India?", 
     "Yes, it is mandatory to wear a helmet while riding a two-wheeler in India.",
    "What is the rule for overtaking on Indian roads?", 
     "Overtaking should always be done from the right side, and it should be ensured that the road ahead is clear for a safe maneuver.",
    "When should a vehicle give way to emergency vehicles?", 
     "Vehicles must give way to emergency vehicles like ambulances, fire engines, and police vehicles by moving to the side of the road to allow them to pass.",
    "What is the significance of a yellow traffic light?", 
     "A yellow traffic light indicates that the signal is about to change to red, and vehicles should slow down and prepare to stop."
])

# Selected chatbot
current_bot = traffic_bot

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/select_dataset', methods=['POST'])
def select_dataset():
    global current_bot
    selected_dataset = request.json.get('dataset')

    if selected_dataset == 'traffic':
        current_bot = traffic_bot
    elif selected_dataset == 'general':
        current_bot = general_bot

    return jsonify(response=f"Dataset switched to {selected_dataset.capitalize()}.")

@app.route('/get_response', methods=['POST'])
def get_bot_response():
    user_message = request.json.get('message')

    if user_message.lower() in ['bye', 'exit', 'ok']:
        return jsonify(response="Thank you for chatting. Goodbye!")

    response = current_bot.get_response(user_message)
    return jsonify(response=str(response))

@app.route('/voice_input', methods=['POST'])
def voice_input():
    samplerate = 44100  # Sampling rate (samples per second)
    duration = 10       # Duration of recording in seconds
    filename = "recorded_audio.wav"  # Output file name

    try:
        # Record audio
        audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished

        # Save the recorded audio as a WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio_data.tobytes())

        # Initialize the recognizer
        recognizer = sr.Recognizer()

        # Load the recorded audio file for transcription
        with sr.AudioFile(filename) as source:
            audio = recognizer.record(source)

        # Perform speech-to-text recognition
        try:
            user_input = recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            user_input = "Google Speech Recognition could not understand the audio"
        except sr.RequestError as e:
            user_input = f"Could not request results from Google Speech Recognition service; {e}"

    finally:
        # Clean up the WAV file
        if os.path.exists(filename):
            os.remove(filename)

    if user_input.lower() in ['bye', 'exit', 'ok']:
        return jsonify(user_input=user_input, response="Thank you for using the Traffic Fine Query Chatbot. Goodbye!")

    # Use current_bot to get the response
    response = current_bot.get_response(user_input)
    return jsonify(user_input=user_input, response=str(response))

if __name__ == '__main__':
    app.run(host='0.0.0.0')

