
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import sys
import os

FREQ_MAP = {
    '00': 17000,
    '01': 17250,
    '10': 17500,
    '11': 17750
}
FREQ_HANDSHAKE = 16000
SAMPLE_RATE = 44100
TONE_DURATION = 0.1  # seconds

def generate_tone(frequency, duration=TONE_DURATION, amplitude=0.5, sample_rate=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone

def encode_message(message):
    bits = ''.join(f'{ord(c):08b}' for c in message)
    if len(bits) % 2 != 0:
        bits += '0'  # pad
    return [bits[i:i+2] for i in range(0, len(bits), 2)]

def transmit_and_save(message, wav_filename="output.wav"):
    symbols = encode_message(message)
    signal = [generate_tone(FREQ_HANDSHAKE)]
    for sym in symbols:
        freq = FREQ_MAP[sym]
        signal.append(generate_tone(freq))
    waveform = np.concatenate(signal)

    # Play
    print("🔊 Transmitting...")
    sd.play(waveform, samplerate=SAMPLE_RATE)
    sd.wait()

    # Save
    int_wave = (waveform * 32767).astype(np.int16)
    wavfile.write(wav_filename, SAMPLE_RATE, int_wave)
    print(f"💾 WAV saved to {wav_filename}")

if __name__ == "__main__":
    try:
        message = input("Enter message to send: ")
        transmit_and_save(message, "4fsk_output.wav")
    except KeyboardInterrupt:
        print("\nTransmission cancelled.")
