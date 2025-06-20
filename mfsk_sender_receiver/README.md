
# 🎧 4-FSK Audio Covert Channel Toolkit

This repository implements a simple but robust **covert communication system** using **4-FSK (4-level Frequency Shift Keying)**. It transmits binary data by modulating audio frequencies and receives/decodes them using FFT analysis.

---

## 📦 Files

| File | Description |
|------|-------------|
| `sender_4fsk_input.py` | Terminal-based sender: enter message, sends tones, and saves `.wav` |
| `sender_4fsk.py`       | Script-based version (no input) |
| `sender_send_wav.py`   | Alternate sender version (same logic, different structure) |
| `receiver_4fsk.py`    | Receiver that can decode from live mic **or** `.wav` file |
| `4fsk_hi.wav`         | Sample encoded message ("Hi") |
| `4fsk_output.wav`     | Another saved transmission |

---

## 🔧 Modulation Details

- **Type:** 4-FSK (4-frequency shift keying)
- **Bits per tone:** 2 bits
- **Tone duration:** 0.1 seconds
- **Sample rate:** 44,100 Hz
- **Amplitude:** 0.5 (normalized)

| Bits | Frequency (Hz) |
|------|----------------|
| `00` | 17000          |
| `01` | 17250          |
| `10` | 17500          |
| `11` | 17750          |

- **Handshake tone:** `16000 Hz` (indicates start of message)

---

## 📤 Transmitter Behavior

1. Converts each character into binary (`8 bits`)
2. Groups bits in pairs → maps to 1 of 4 frequencies
3. Prepends a **handshake tone** at 16000 Hz
4. Plays the signal + saves it as `.wav` file

---

## 📥 Receiver Behavior

- Supports:
  - 🎧 Live microphone input
  - 📂 `.wav` file decoding
- Performs:
  1. Chunked FFT (0.1s window)
  2. Frequency peak detection
  3. Tolerance matching ±100 Hz
  4. Bitstream reconstruction
  5. Message reassembly from 8-bit chunks

---

## 🧪 How to Use

### ▶️ Send and Save Message:
```bash
python sender_4fsk_input.py
```
You'll be prompted:
```
Enter message to send:
```
A file `4fsk_output.wav` will be saved.

### 🧾 Receive from File:
```bash
python receiver_4fsk.py 4fsk_output.wav
```

### 🎙️ Receive Live:
```bash
python receiver_4fsk.py
```

---

## 🧠 Notes for Engineers

- **Modulation technique**: Digital baseband → audio carrier (4-FSK)
- **Spectral footprint**: 16–18 kHz (ultrasound-capable)
- **Signal processing**:
  - FFT-based peak detection
  - Tolerance-based matching
- **Security/Covert Context**:
  - Inspired by academic covert channel designs
  - Can be adapted for CPU-load or EM-based signaling

---

## 📈 Future Ideas

- Add error correction (e.g., Hamming, CRC)
- Add sync framing (preamble, length)
- Switch to OFDM or M-FSK
- Apply to SDR hardware (e.g., loop antenna, mic)

---

