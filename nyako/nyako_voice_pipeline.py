import pyaudio
from IPython.display import clear_output
from IPython.display import display
from time import sleep
import numpy as np
import torchaudio

from LLM.nyako_llm import ConversationSession
from nyako_te import enhance
from nyako_stt import transcribeSpeech
from nyako_vad import detectVoiceActivity
from nyako_tts import say

import torch
torch.set_num_threads(3)

# audio subsystem         
audio = pyaudio.PyAudio()

from params import nyako_prompt
session = ConversationSession(nyako_prompt)

# counter for how long there has been no speech input
noSpeechTime = 0
speechRecordingTriggered = False
speechBuffer = bytes()
def microphoneInputCallback(in_data, frame_count, time_info, status):
    isSpeakingProbability = detectVoiceActivity(in_data)

    global speechRecordingTriggered
    global noSpeechTime
    global speechBuffer

    if isSpeakingProbability > 0.5 and not speechRecordingTriggered:
        speechRecordingTriggered = True

    if speechRecordingTriggered:
        speechBuffer += in_data

    if isSpeakingProbability < 0.5:
        # one buffer without speech is 32ms
        noSpeechTime += 0.032
        # if there hasn't been speech for 1 second and speech has been recorded
        if noSpeechTime > 1 and speechRecordingTriggered:
            speechRecordingTriggered = False
            noSpeechTime = 0

            recordedText = transcribeSpeech(speechBuffer)
            print("Recorded Text: " + recordedText)

            # clear buffer after STT
            speechBuffer = bytes()

            # make sure text is not empty
            if recordedText == "":
                return (in_data, pyaudio.paContinue)

            # non-alphanumeric leading characters seem to crash this
            #recordedText = enhance(recordedText)
            #print("Enhanced Text: " + recordedText)

            #response = session.query("[Voice In] " + recordedText)
            #print("Response: " + response)

            #say(response)
    else:
        noSpeechTime = 0
    
    return (in_data, pyaudio.paContinue)

#print("Warming up...")
#from nyako_warmup import warmup
#warmup()

print("Nyako listening...")
# starts main loop
from params import FramesPerBuffer, INPUT_SAMPLING_RATE
stream = audio.open(rate=INPUT_SAMPLING_RATE, channels=1, input=True, format=pyaudio.paFloat32, frames_per_buffer=FramesPerBuffer, stream_callback=microphoneInputCallback)

# clear ipynb output
clear_output()

while stream.is_active():
    sleep(0.1)
 
stream.close()

audio.terminate()