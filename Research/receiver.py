import csv
import math
import numpy as np

################################################################
#                USER CONFIGURATION / TUNING
################################################################
# If you know your transmitter toggles a specific frequency, set it here:
TARGET_FREQ = 300_000_000   # e.g. 300 MHz
FREQ_TOL = 100_000          # ± 100 kHz tolerance around target

# If you do NOT know the exact toggled frequency, set below to True,
# and script tries to find a bin with the largest amplitude variability.
AUTO_DETECT_FREQ = False

# If you know approximate bit time, or how often your sender toggles:
BIT_TIME_EST = 0.05  # e.g. 50ms

# Threshold for deciding '1' vs '0' in dB. Adjust as needed.
AMP_THRESHOLD = -70.0

# If your transmitter uses a known preamble (like '10101010'):
PREAMBLE = '10101010'

################################################################
#         CSV PARSING + FREQUENCY BIN EXTRACTION
################################################################

def parse_hackrf_sweep(csv_file):
    """
    Generator yielding each line with (timestamp, freq_start, freq_step, amplitude_list).
    """
    import csv
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            # skip empty/incomplete lines
            if len(row) < 7:
                continue
            try:
                date_str    = row[0]  # '2025-04-02'
                time_str    = row[1]  # '15:23:00.907466'
                freq_start  = float(row[2])  # e.g. 290000000
                freq_end    = float(row[3])  # e.g. 295000000
                freq_step   = float(row[4])  # e.g. 1666666.67
                sample_ct   = int(row[5])    # e.g. 12

                # amplitude readings in dB, e.g. [-43.48, -47.3, -49.27]
                amps = row[6:]
                amps_floats = [float(a) for a in amps]

                timestamp = f"{date_str} {time_str}"
                yield (timestamp, freq_start, freq_step, amps_floats)

            except (ValueError, IndexError):
                # skip lines that fail parse
                continue


def find_bin_for_freq(freq_start, freq_step, num_bins, target_freq):
    """
    Return the index of the bin whose center freq is closest to target_freq,
    or None if out of range.
    """
    freq_end = freq_start + freq_step * (num_bins - 1)
    if target_freq < freq_start or target_freq > freq_end:
        return None
    approx_idx = int(round((target_freq - freq_start) / freq_step))
    if approx_idx < 0 or approx_idx >= num_bins:
        return None
    return approx_idx

################################################################
#       MAIN DECODER LOGIC
################################################################

def decode_sweep(csv_path):
    """
    - If AUTO_DETECT_FREQ = False, uses TARGET_FREQ to pick a bin
      and extracts amplitude over time. Then threshold -> bits.
    - If AUTO_DETECT_FREQ = True, tries to find which bin has the
      largest amplitude variation, picks that, and decodes it.
    - Returns a string with the recovered bits or partial message.
    """

    # 1) Collect amplitude over time for all bins (if auto-detect).
    bin_data_map = {}  # bin_index -> list of (time_in_seconds, amp_db)
    times = []         # we'll store each line's approx time for bit grouping

    # We'll keep track of the first line's time to create relative timestamps.
    start_time = None

    # For rough time extraction, parse 'HH:MM:SS.ssssss' from row[1]
    def parse_time_str(t_str):
        # e.g. '12:34:56.789012'
        hh, mm, ss_frac = t_str.split(':')
        ss, frac = ss_frac.split('.') if '.' in ss_frac else (ss_frac, '0')
        h = int(hh)
        m = int(mm)
        s = int(ss)
        micro = int(frac[:6].ljust(6,'0'))  # microseconds
        total_sec = h*3600 + m*60 + s + micro/1_000_000
        return total_sec

    # pass 1: parse CSV lines
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 7:
                continue
            try:
                date_str = row[0]   # 'YYYY-MM-DD'
                time_str = row[1]   # 'HH:MM:SS.ssssss'
                freq_start = int(row[2])
                freq_end   = int(row[3])
                freq_step  = int(row[4])
                amps_str   = row[6:]  # amplitude array
            except:
                continue

            # compute approximate time offset
            t_sec = parse_time_str(time_str)
            if start_time is None:
                start_time = t_sec
            rel_time = t_sec - start_time

            # store in bin_data_map
            for i, amp_s in enumerate(amps_str):
                try:
                    amp_db = float(amp_s)
                except ValueError:
                    amp_db = float('nan')
                if i not in bin_data_map:
                    bin_data_map[i] = []
                bin_data_map[i].append((rel_time, amp_db))

    # If no data, abort
    if not bin_data_map:
        print("No valid data found in CSV.")
        return ""

    # 2) If we are auto-detecting which bin toggles, find bin with largest stddev or range.
    chosen_bin = None
    if AUTO_DETECT_FREQ:
        best_bin = None
        best_var = 0
        for b_idx, arr in bin_data_map.items():
            # compute amplitude stdev or range
            amps = [p[1] for p in arr if not math.isnan(p[1])]
            if len(amps) < 2:
                continue
            # measure variance or difference
            var_ = np.var(amps)
            if var_ > best_var:
                best_var = var_
                best_bin = b_idx
        chosen_bin = best_bin
        print(f"AUTO-DETECT: Found bin {chosen_bin} with largest variance {best_var:.2f}")
    else:
        # 2b) If we have a known target freq, find the bin that’s closest to it
        #    from the first line’s freq_start/freq_step. We'll guess row 0 or similar.
        #    Actually we can do it from any row, but let's do a quick approach.
        sample_bin_keys = sorted(bin_data_map.keys())
        freq_start_guess = 290_000_000
        freq_step_guess = 20_000
        # If you know from hackrf_sweep the typical step, you can refine.
        # We'll pick the middle row's freq start/step for a guess:
        # For a simpler approach, just manually set freq_start/step or
        # parse them from an actual line. We'll do an approximation:
        freq_start_guess = 290_000_000
        freq_step_guess = 200_000  # e.g. if you used -w 2000000, then each line can have multiple bins

        # We'll assume the bin index is:
        b_idx = int(round((TARGET_FREQ - freq_start_guess)/freq_step_guess))
        # That might be off if your actual step is different. Let's just pick it:
        chosen_bin = b_idx
        print(f"Using bin index {chosen_bin} for target freq ~ {TARGET_FREQ/1e6} MHz")

    if chosen_bin not in bin_data_map:
        print(f"Chosen bin {chosen_bin} not found in data. Possibly out-of-range or mismatch.")
        return ""

    # 3) Extract amplitude/time for the chosen bin
    raw_data = bin_data_map[chosen_bin]
    # sort by time
    raw_data.sort(key=lambda x: x[0])
    # raw_data is now a list of (rel_time, amp_db)
    if len(raw_data) < 2:
        print("Not enough data in chosen bin to decode.")
        return ""

    # 4) Convert amplitude -> bits over time
    #    We'll chunk the timeline in ~BIT_TIME_EST increments, take average amplitude
    #    in that chunk, then threshold => '1' or '0'.
    bit_list = []
    chunk_start = raw_data[0][0]
    chunk_amps = []

    def finalize_chunk_amps(amps):
        if not amps:
            return None
        mean_amp = np.mean(amps)
        return '1' if mean_amp > AMP_THRESHOLD else '0'

    current_idx = 0
    while current_idx < len(raw_data):
        t, amp = raw_data[current_idx]
        # if we're still within chunk range
        if t < chunk_start + BIT_TIME_EST:
            if not math.isnan(amp):
                chunk_amps.append(amp)
            current_idx += 1
        else:
            # finalize chunk
            bit = finalize_chunk_amps(chunk_amps)
            if bit is not None:
                bit_list.append(bit)
            # shift chunk_start
            chunk_start += BIT_TIME_EST
            chunk_amps = []

    # finalize last chunk
    bit = finalize_chunk_amps(chunk_amps)
    if bit is not None:
        bit_list.append(bit)

    bitstream = ''.join(bit_list)
    print(f"Extracted bitstream (raw): {bitstream[:200]}{'...' if len(bitstream) > 200 else ''}")

    # 5) Search for repeating pattern or preamble
    # If your transmitter is repeating '10101010 + message', we look for that
    # example:
    idx = bitstream.find(PREAMBLE)
    if idx == -1:
        print("No preamble found in bitstream.")
        return bitstream
    # else, parse after preamble
    payload_start = idx + len(PREAMBLE)
    # If you know how many bits your message has, extract them. If not, just collect the rest.
    # e.g. transmitter was 'Hello' => 5 chars => 5 * 8 bits = 40
    #     plus the preamble => total 48 bits

    # Let's guess 5 chars: 'Hello' => 40 bits
    # Adjust to your actual message length
    msg_bits = bitstream[payload_start : payload_start + 40]
    if len(msg_bits) < 40:
        print("Not enough bits for full message.")
        return bitstream

    # Convert each 8 bits to a char
    message = []
    for i in range(0, len(msg_bits), 8):
        chunk = msg_bits[i:i+8]
        val = int(chunk, 2)
        message.append(chr(val))
    final_msg = ''.join(message)
    print(f"Decoded message: {final_msg}")
    return final_msg

################################################################
#                       MAIN CLI
################################################################

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} emf_sweep.csv")
        sys.exit(1)
    csv_file = sys.argv[1]
    result = decode_sweep(csv_file)
    print("Done.")
