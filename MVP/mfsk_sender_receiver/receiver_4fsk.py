import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
import sys
import os

# Frequencies mapped to 2-bit symbols
FREQ_MAP = {
    17000: '00',
    17250: '01',
    17500: '10',
    17750: '11'
}
FREQ_HANDSHAKE = 16000
TOLERANCE = 100  # Hz
CHUNK_SIZE = 4410  # 0.1s at 44100 Hz
SAMPLE_RATE = 44100

def detect_frequency(data, sample_rate=SAMPLE_RATE):
    fft = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(fft), 1 / sample_rate)
    magnitude = np.abs(fft)
    peak_idx = np.argmax(magnitude)
    peak_freq = abs(freqs[peak_idx])
    return peak_freq

def listen(duration=5, sample_rate=SAMPLE_RATE):
    print("🔴 Listening for", duration, "seconds...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float64')
    sd.wait()
    return recording.flatten()

def decode_signal(signal, sample_rate=SAMPLE_RATE):
    bits = ''
    handshake_received = False

    for i in range(0, len(signal), CHUNK_SIZE):
        chunk = signal[i:i + CHUNK_SIZE]
        if len(chunk) < CHUNK_SIZE:
            break
        freq = detect_frequency(chunk, sample_rate)

        if not handshake_received:
            if abs(freq - FREQ_HANDSHAKE) < TOLERANCE:
                handshake_received = True
        else:
            matched = False
            for target_freq, bit_pair in FREQ_MAP.items():
                if abs(freq - target_freq) < TOLERANCE:
                    bits += bit_pair
                    matched = True
                    break
            if not matched:
                # Skip or log unknown tone
                pass

    return bits

def bits_to_message(bits):
    chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8) if len(bits[i:i+8]) == 8]
    return ''.join(chars)

def receive_and_decode():
    signal = listen()
    bits = decode_signal(signal)
    msg = bits_to_message(bits)
    print("✅ Decoded message:", msg)

def decode_from_wav(filepath):
    if not os.path.isfile(filepath):
        print(f"❌ File not found: {filepath}")
        return
    sample_rate, data = wavfile.read(filepath)
    if data.ndim > 1:
        data = data[:, 0]  # Use first channel if stereo
    data = data.astype(np.float64) / 32767
    bits = decode_signal(data, sample_rate)
    msg = bits_to_message(bits)
    print("✅ Decoded from WAV:", msg)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        decode_from_wav(sys.argv[1])
    else:
        receive_and_decode()
