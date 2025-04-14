
import numpy as np
import sounddevice as sd

FREQ_MAP = {
    '00': 17000,
    '01': 17250,
    '10': 17500,
    '11': 17750
}
FREQ_HANDSHAKE = 16000

def generate_tone(frequency, duration=0.1, amplitude=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone

def encode_message(message):
    bits = ''.join(f'{ord(char):08b}' for char in message)
    if len(bits) % 2 != 0:
        bits += '0'  # pad to even
    return [bits[i:i+2] for i in range(0, len(bits), 2)]

def transmit(message):
    symbols = encode_message(message)
    signal = [generate_tone(FREQ_HANDSHAKE)]

    for symbol in symbols:
        freq = FREQ_MAP[symbol]
        signal.append(generate_tone(freq))
    
    sound = np.concatenate(signal)
    sd.play(sound, samplerate=44100)
    sd.wait()
