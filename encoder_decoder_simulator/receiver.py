import pandas as pd

def is_transmission(sweep, preamble_start=100, preamble_end=130, marker_threshold=-60):
    """
    Determines if a given sweep is a transmission.
    The preamble (rows 100–129) should contain strong bursts (e.g. -40 dB).
    If the average dB in that region is above marker_threshold, we classify it as a transmission.
    """
    preamble = sweep.iloc[preamble_start:preamble_end]
    avg_dB = preamble['dB'].mean()
    return avg_dB > marker_threshold  # marker_threshold should be well above baseline (-90)

def decode_message_from_sweep(sweep, 
                              message_region_start=130, message_region_end=870,
                              mid_threshold=-60):
    """
    Decodes the message from a transmission sweep.
      - Assumes the message is encoded in rows 130–869.
      - Each row in that region is interpreted as a bit:
          If dB > mid_threshold → '1', otherwise '0'.
      - The resulting binary string is split into 8-bit groups and converted to ASCII.
    """
    message_region = sweep.iloc[message_region_start:message_region_end]
    bits = []
    for db_val in message_region['dB']:
        bits.append('1' if db_val > mid_threshold else '0')
    binary_str = "".join(bits)
    # Trim the binary string to a multiple of 8 bits.
    n = len(binary_str) - (len(binary_str) % 8)
    binary_str = binary_str[:n]
    message = ""
    for i in range(0, len(binary_str), 8):
        byte_str = binary_str[i:i+8]
        try:
            message += chr(int(byte_str, 2))
        except Exception:
            message += '?'
    return message

def decode_sweeps(input_csv="sweeps.csv"):
    """
    Reads the CSV file containing continuous sweeps and decodes transmissions.
    For each sweep (grouped by Timestamp):
      - If the preamble region (rows 100–129) has strong markers, the sweep is treated as a transmission.
      - The message region (rows 130–869) is then decoded into a binary string and converted to text.
      - Otherwise, the sweep is considered silence.
    Returns a DataFrame with Timestamp and Decoded Message (empty for silence).
    """
    df = pd.read_csv(input_csv)
    transmissions = []
    
    # Group sweeps by Timestamp.
    for ts, group in df.groupby("Timestamp"):
        # Sort by Frequency_MHz to ensure proper order.
        sweep = group.sort_values("Frequency_MHz").reset_index(drop=True)
        if len(sweep) < 900:
            transmissions.append({"Timestamp": ts, "Message": ""})
            continue
        
        if is_transmission(sweep):
            message = decode_message_from_sweep(sweep)
            print(f"Decoded transmission at {ts}: {message}")
        else:
            message = ""
            print(f"Silence sweep at {ts}.")
        transmissions.append({"Timestamp": ts, "Message": message})
    
    return pd.DataFrame(transmissions)

if __name__ == "__main__":
    decoded_df = decode_sweeps("sweeps.csv")
    print("Decoded transmissions:")
    print(decoded_df)

