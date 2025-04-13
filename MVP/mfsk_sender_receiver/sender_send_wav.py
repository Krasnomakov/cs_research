import scipy.io.wavfile as wavfile
import numpy as np

# Helper from sender_4fsk to generate tone
def generate_tone(frequency, duration=0.1, amplitude=0.5, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    return tone

# Mapping from 2-bit symbols to frequencies
FREQ_MAP = {
    '00': 17000,
    '01': 17250,
    '10': 17500,
    '11': 17750
}
FREQ_HANDSHAKE = 16000
SAMPLE_RATE = 44100

# Message to encode
message = "Hi"
bits = ''.join(f'{ord(c):08b}' for c in message)
if len(bits) % 2 != 0:
    bits += '0'
symbols = [bits[i:i+2] for i in range(0, len(bits), 2)]

# Generate waveform
signal = [generate_tone(FREQ_HANDSHAKE)]
for sym in symbols:
    freq = FREQ_MAP[sym]
    signal.append(generate_tone(freq))

final_wave = np.concatenate(signal)

# Normalize and save as WAV
final_wave = (final_wave * 32767).astype(np.int16)
wav_path = "4fsk_hi.wav"
wavfile.write(wav_path, SAMPLE_RATE, final_wave)

wav_path

