# Minimal Viable Products (MVPs) for Covert Channels and Communication Systems

This directory contains a collection of minimal viable products (MVPs) that explore different methods of creating communication systems, with a focus on covert channels. Each sub-project demonstrates a unique approach to transmitting and receiving data, using different physical or simulated mediums.

---

## Projects

Below is a summary of the projects included in this directory.

### 1. [Encoder/Decoder Simulator](./encoder_decoder_simulator/)

*   **Description**: This project simulates an RF transmission system using frequency sweeps. A sender encodes messages by modulating power levels within the sweeps, and a receiver decodes them from a CSV file.
*   **Technology**: Python, Frequency Sweeps, Power-Level Encoding.
*   **Medium**: Simulated RF (CSV file).

### 2. [Working Pair - CPU-based EM Covert Channel](./working_pair/)

*   **Description**: An implementation of a covert channel that uses CPU load modulation on a Raspberry Pi 4 to generate electromagnetic (EM) emissions. It demonstrates a simple air-gap communication link using On-Off Keying (OOK).
*   **Technology**: C (Transmitter), Python (Receiver), GQRX, On-Off Keying (OOK).
*   **Medium**: Electromagnetic (EM) emissions.

### 3. [4-FSK Audio Covert Channel](./mfsk_sender_receiver/)

*   **Description**: A covert communication system using 4-FSK (4-level Frequency Shift Keying) to transmit data over an audio channel. The system can send and receive messages using audio tones, with the receiver supporting both live microphone input and `.wav` files.
*   **Technology**: Python, 4-FSK, FFT Analysis.
*   **Medium**: Audio.

---

For more detailed information, please refer to the `README.md` file within each project's directory.
