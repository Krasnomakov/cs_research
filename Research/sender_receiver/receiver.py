import csv
import math

# CONFIG
TARGET_FREQ = 260_000_000  # 260 MHz
FREQ_TOL = 10_000          # ±10 kHz window
AMP_THRESHOLD = -70.0      # dB threshold for 'bit=1'
PREAMBLE = '10101010'      # from transmitter
BITS_PER_BYTE = 8
# If your transmitter has a known bit time ~0.01 s, you might adapt grouping windows, etc.

def parse_hackrf_sweep(csv_file):
    """
    Generator yielding (timestamp, freq_start, freq_step, amp_list) for each line
    from hackrf_sweep CSV output. You may need to adjust parsing logic if your CSV
    columns differ in order/format.
    """
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # Example row structure assumption:
            # row[0] = date (YYYY-MM-DD)
            # row[1] = time (HH:MM:SS.ssssss)
            # row[2] = start_freq (Hz)
            # row[3] = end_freq (Hz)
            # row[4] = freq_step (Hz)
            # row[5] = sample_count
            # row[6..] = amplitude readings in dB
            try:
                date_str = row[0]
                time_str = row[1]
                freq_start = int(row[2])
                freq_end   = int(row[3])
                freq_step  = int(row[4])
                sample_ct  = int(row[5])
                amplitude_data = row[6:]  # list of dB readings

                # Combine date_str + time_str if needed or just keep time_str
                # Convert to float seconds or something if we want a single timestamp
                # For simplicity, let's store time as "date time" string
                timestamp = f'{date_str} {time_str}'

                yield (timestamp, freq_start, freq_step, amplitude_data)
            except (ValueError, IndexError):
                # Skip lines that don't parse well (comments, incomplete lines)
                continue

def freq_index_for_target(freq_start, freq_step, num_bins, target):
    """
    Find which bin index is closest to 'target' frequency.
    Return None if out of range.
    """
    freq_end = freq_start + freq_step * (num_bins - 1)
    if target < freq_start or target > freq_end:
        return None  # target freq not in this line's range
    # approximate index
    approx_idx = int(round((target - freq_start) / freq_step))
    return approx_idx

def decode_csv_sweep(csv_file):
    """
    Decode an OOK-based bitstream from hackrf_sweep CSV data.
    1) For each line, find amplitude near TARGET_FREQ
    2) Convert to bit (1/0) with threshold
    3) Reassemble bits into preamble + message
    """
    bits = ''
    in_preamble = False
    message_bits = ''
    decoded_message = ''

    for (timestamp, freq_start, freq_step, amp_list) in parse_hackrf_sweep(csv_file):
        num_bins = len(amp_list)
        idx = freq_index_for_target(freq_start, freq_step, num_bins, TARGET_FREQ)
        if idx is None or idx >= num_bins:
            continue

        try:
            # Extract amplitude in dB for that bin
            amp_db = float(amp_list[idx])
        except ValueError:
            continue

        # Convert amplitude to bit
        bit = '1' if amp_db > AMP_THRESHOLD else '0'
        bits += bit

        # Look for preamble
        if not in_preamble:
            # We only check the last 8 bits
            if len(bits) >= len(PREAMBLE):
                if bits[-len(PREAMBLE):] == PREAMBLE:
                    in_preamble = True
                    message_bits = ''  # reset for new message
        else:
            # Already found preamble => build message bits
            message_bits += bit

            # If we suspect the transmitter loops or has known message length,
            # we can parse in full bytes when we see them. E.g.:
            if len(message_bits) % BITS_PER_BYTE == 0:
                # Reconstruct the last 8 bits
                byte_bits = message_bits[-BITS_PER_BYTE:]
                char_val = int(byte_bits, 2)
                # Keep only printable range or do other checks
                decoded_message += chr(char_val)
                # [Optional] if you know message length or see special terminator
                # you can stop or parse.

    return decoded_message

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f\"Usage: python {sys.argv[0]} emf_sweep.csv\")
        sys.exit(1)

    csv_file = sys.argv[1]
    msg = decode_csv_sweep(csv_file)
    print(\"Decoded message:\", msg)
