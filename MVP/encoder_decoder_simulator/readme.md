# RF Sweep Encoder & Decoder

This project demonstrates a simulation of an RF transmission system using frequency sweeps, complete with a sender that encodes messages into the sweeps and a receiver that decodes them from a CSV file.

---

## Table of Contents
1. [Project Overview](#project-overview)  
2. [File Descriptions](#file-descriptions)  
3. [Installation](#installation)  
4. [Usage](#usage)  
5. [License](#license)

---

## Project Overview

### What It Does
- **Sender**: Generates RF sweeps (1000 data points, from 300–301 MHz) and encodes a rotating set of sentences.  
- **Transmissions**: Marked by preamble/postamble regions set to -40 dB. Between these markers lies a message region encoding bits at different power levels:
  - `-50 dB` for binary `1`
  - `-70 dB` for binary `0`
- **Receiver**: Reads the CSV file containing the recorded sweeps, identifies valid transmissions by locating the markers, then decodes the embedded message.

### Why It Matters
This setup serves as a simple demonstration of how frequency sweeps and power-level encoding can transmit arbitrary text messages. It simulates the real-world process of encoding and decoding signals based on their power spectral content.

---

## File Descriptions

- **sender.py**  
  Continuously generates frequency sweeps with randomized intervals of silence. Each sweep is appended to `sweeps.csv` in real time.  
  - **Preamble (rows 100–129)**  
  - **Postamble (rows 870–899)**  
  - **Message Region (rows 130–869)**

- **decoder.py**  
  Reads `sweeps.csv`, groups records by timestamp, locates valid transmissions (using preamble/postamble markers), and decodes the message bits in the message region.

- **sweeps.csv**  
  A continuously growing CSV that holds the sweep data (power levels) and corresponding timestamps.

---

## Installation

1. **Python 3.x**  
   Ensure you have Python 3.x installed.

2. **Dependencies**  
   Install the following packages:
   ```bash
   pip install numpy pandas

## Usage

### Run the Sender
In a terminal, start the sender to continuously transmit and log sweeps:
```bash
python sender.py

### Run the Decoder
After collecting some sweep data, run the decoder in a separate terminal:
```bash
python decoder.py
