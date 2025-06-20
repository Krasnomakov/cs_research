# Covert Communication & Advanced Signaling Systems

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![C](https://img.shields.io/badge/C-00599C?style=for-the-badge&logo=c&logoColor=white)
![Shell Script](https://img.shields.io/badge/Shell_Script-121011?style=for-the-badge&logo=gnu-bash&logoColor=white)
![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)

A collection of minimal viable products (MVPs) exploring diverse methods of creating communication systems, with a special focus on covert channels and advanced signaling techniques.

---

## 🚀 Projects

Here's a breakdown of the projects in this repository.

---

### 1. RF Sweep Encoder & Decoder Simulator

> This project simulates an RF transmission system using frequency sweeps. A sender encodes messages by modulating power levels within the sweeps, and a receiver decodes them from a CSV file.

*   **Medium**: Simulated RF (CSV file)
*   **Technology Stack**:
    *   ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
    *   **Libraries**: NumPy, Pandas
*   **How it Works**:
    *   **Sender**: Generates frequency sweeps (300–301 MHz) and encodes binary data by modulating power levels (`-50 dB` for `1`, `-70 dB` for `0`).
    *   **Receiver**: Reads a `sweeps.csv` file, detects transmission markers (preamble/postamble), and decodes the power-level encoded message.

---

### 2. CPU-based EM Covert Channel

> An implementation of a covert channel that uses CPU load modulation on a Raspberry Pi 4 to generate electromagnetic (EM) emissions. It demonstrates a simple air-gap communication link using On-Off Keying (OOK).

*   **Medium**: Electromagnetic (EM) Emissions
*   **Technology Stack**:
    *   ![C](https://img.shields.io/badge/C-00599C?style=for-the-badge&logo=c&logoColor=white)
    *   ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
    *   **Tools**: GQRX, Telnet
*   **How it Works**:
    *   **Transmitter (C)**: Runs on a Raspberry Pi 4, modulating CPU load to create EM fields. High CPU load (`1`) vs. Idle (`0`).
    *   **Receiver (Python)**: Connects to GQRX via TCP/IP to monitor signal strength and decode the OOK-modulated bits from the EM emissions.

---

### 3. 4-FSK Audio Covert Channel

> A covert communication system using 4-FSK (4-level Frequency Shift Keying) to transmit data over an audio channel. The system can send and receive messages using audio tones, with the receiver supporting both live microphone input and `.wav` files.

*   **Medium**: Audio
*   **Technology Stack**:
    *   ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
    *   **Techniques**: 4-FSK, FFT Analysis
*   **How it Works**:
    *   **Transmitter**: Converts text to binary, maps pairs of bits to one of four audio frequencies (17000-17750 Hz), and plays them as tones.
    *   **Receiver**: Uses FFT on audio input (live or from a `.wav` file) to detect frequency peaks, reconstruct the bitstream, and decode the message.

---

## 🛠️ Skills & Technologies Showcase

This collection demonstrates a variety of skills and technologies, including:

*   **Programming Languages**: Python, C
*   **Digital Signal Processing (DSP)**:
    *   Frequency Shift Keying (FSK)
    *   On-Off Keying (OOK)
    *   Fast Fourier Transform (FFT) for spectral analysis
*   **Covert Channel Techniques**:
    *   CPU Load Modulation
    *   Electromagnetic (EM) Side-Channel Analysis
    *   Audio Steganography
*   **Hardware Interfacing**: Raspberry Pi, SDR (via GQRX)
*   **Data Handling**: Real-time data logging (CSV), file I/O, audio stream processing.

---

For more detailed information, please refer to the `README.md` file within each project's directory.