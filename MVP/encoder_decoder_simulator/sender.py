import numpy as np
import pandas as pd
import time
import random
from datetime import datetime

def text_to_binary(text):
    """Convert text into a binary string (8 bits per character)."""
    return ''.join(format(ord(c), '08b') for c in text)

def encode_transmission(message, sweep_length=1000, freq_start=300.0, freq_end=301.0):
    """
    Encodes a transmission sweep that contains:
      - A preamble (rows 100–129): strong bursts at -40 dB.
      - A message region (rows 130–869): each row encodes one bit.
         • '1' is represented by -50 dB.
         • '0' is represented by -70 dB.
         The message binary is truncated to at most 740 bits (92 bytes).
      - A postamble (rows 870–899): strong bursts at -40 dB.
      - All other rows (0–99, 900–999) remain at a baseline of -90 dB.
      
    Returns a DataFrame with columns:
      Frequency_MHz, dB, Timestamp.
    """
    num_points = sweep_length
    freqs = np.linspace(freq_start, freq_end, num_points)
    dB = np.full(num_points, -90.0)  # baseline everywhere

    # Define encoding region boundaries.
    encoding_start = 100
    encoding_end = 900

    # Preamble: rows 100-129 → set to -40 dB (start marker).
    preamble_start = encoding_start
    preamble_end = preamble_start + 30
    dB[preamble_start:preamble_end] = -40.0

    # Postamble: rows 870-899 → set to -40 dB (stop marker).
    postamble_end = encoding_end
    postamble_start = postamble_end - 30
    dB[postamble_start:postamble_end] = -40.0

    # Message region: rows 130-869 (740 rows available).
    message_region_start = preamble_end  # row 130
    message_region_end = postamble_start   # row 870
    available_bits = message_region_end - message_region_start  # 740 bits

    binary_message = text_to_binary(message)
    if len(binary_message) > available_bits:
        print(f"Warning: message is {len(binary_message)} bits; truncating to {available_bits} bits.")
        binary_message = binary_message[:available_bits]

    # For each bit, set the corresponding row:
    # '1' → -50 dB; '0' → -70 dB.
    for i, bit in enumerate(binary_message):
        row = message_region_start + i
        dB[row] = -50.0 if bit == '1' else -70.0

    # Create DataFrame for the sweep.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame({
        "Frequency_MHz": freqs,
        "dB": dB,
        "Timestamp": timestamp
    })
    return df

def encode_silence(sweep_length=1000, freq_start=300.0, freq_end=301.0):
    """Generates a sweep that is completely silent (baseline -90 dB)."""
    num_points = sweep_length
    freqs = np.linspace(freq_start, freq_end, num_points)
    dB = np.full(num_points, -90.0)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame({
        "Frequency_MHz": freqs,
        "dB": dB,
        "Timestamp": timestamp
    })
    return df

def sender_loop(output_csv="sweeps.csv"):
    """
    Continuously sends sweeps.
      - In each loop, the system randomly decides to send a transmission sweep or a silence sweep.
      - For transmission sweeps, it rotates among 3 sentences.
      - Transmission sweeps embed a preamble (start marker) and postamble (stop marker)
        that the receiver will use to locate and decode the message region.
      - Each sweep is appended to the output CSV.
      - A random wait (1–3 seconds) is introduced between sweeps.
    """
    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Pack my box with five dozen liquor jugs.",
        "How vexingly quick daft zebras jump!"
    ]
    sentence_index = 0
    first = True
    while True:
        # Randomly choose the mode (e.g., 40% chance to transmit).
        mode = "transmission" if random.random() < 0.4 else "silence"
        if mode == "transmission":
            message = sentences[sentence_index]
            sentence_index = (sentence_index + 1) % len(sentences)
            df_sweep = encode_transmission(message)
            print(f"Transmission sweep sent: {message}")
        else:
            df_sweep = encode_silence()
            print("Silence sweep sent.")

        # Append the sweep to the CSV file.
        if first:
            df_sweep.to_csv(output_csv, index=False, mode='w')
            first = False
        else:
            df_sweep.to_csv(output_csv, index=False, mode='a', header=False)
        
        # Wait a random period between 1 and 3 seconds.
        time.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    sender_loop()

