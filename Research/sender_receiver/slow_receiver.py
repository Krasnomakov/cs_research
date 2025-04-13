#!/usr/bin/env python3
"""
Slow Receiver for the 5-second CPU load signals.
Parses hackrf_sweep CSV, chunk by 5 seconds,
checks average amplitude => '1' or '0'.
"""

import csv
import math
import numpy as np

TARGET_FREQ = 300_000_000  # e.g. 300 MHz in your range
AMP_THRESHOLD = -42.0      # adjust based on your environment
BIT_DURATION  = 5.0        # MUST match sender
CHUNK_PADDING = 0.0        # small overlap if needed
START_TIME    = None       # we figure out from CSV
AUTO_DETECT_BIN = True     # If True, pick bin with largest variance
                           # Else, we do an approximate bin for TARGET_FREQ

def parse_time_str(date_str, time_str):
    """
    date_str = '2025-04-02'
    time_str = '15:23:00.907466'
    Convert to float seconds from the first line
    """
    # Minimal approach: parse time only (assuming same day).
    # If hackrf_sweep includes day changes, you'll need a real datetime parse
    h, m, sfrac = time_str.split(':')
    s, frac = sfrac.split('.') if '.' in sfrac else (sfrac, '0')
    hh = int(h)
    mm = int(m)
    ss = int(s)
    micro = int(frac[:6].ljust(6,'0'))
    total_sec = hh*3600 + mm*60 + ss + micro/1_000_000
    return total_sec

def parse_sweep(csv_file):
    """
    Return a dictionary: bin_index -> list of (time_s, amp_db)
    The columns are:
    0 date_str
    1 time_str
    2 freq_start
    3 freq_end
    4 freq_step
    5 sample_count
    6... => amplitude readings
    """
    bin_map = {}  # bin_index => list of (time, amplitude)
    start_time = None

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 7:
                continue
            try:
                date_str   = row[0].strip()
                time_str   = row[1].strip()
                freq_start = float(row[2])
                freq_end   = float(row[3])
                freq_step  = float(row[4])
                sample_ct  = int(row[5])
                amps_str   = row[6:]
            except ValueError:
                continue

            # parse time
            t_sec = parse_time_str(date_str, time_str)
            if start_time is None:
                start_time = t_sec
            rel_t = t_sec - start_time

            # convert amplitude strings to floats
            amps = []
            for a_str in amps_str:
                try:
                    amps.append(float(a_str))
                except ValueError:
                    amps.append(float('nan'))

            # store in bin_map
            for i, amp_db in enumerate(amps):
                if i not in bin_map:
                    bin_map[i] = []
                bin_map[i].append((rel_t, amp_db, freq_start, freq_step))
    return bin_map

def freq_of_bin(freq_start, freq_step, bin_offset):
    return freq_start + bin_offset * freq_step

def find_active_bin(bin_map):
    """
    If AUTO_DETECT_BIN, we find the bin with the largest variance in amplitude.
    Otherwise, we approximate which bin corresponds to TARGET_FREQ.
    This is very rough, as hackrf_sweep lines might be chunked out of order.
    """
    if AUTO_DETECT_BIN:
        best_bin = None
        best_var = 0.0
        for b_idx, data_list in bin_map.items():
            # ignore NaN
            amps = [d[1] for d in data_list if not math.isnan(d[1])]
            if len(amps) < 2:
                continue
            var_ = np.var(amps)
            if var_ > best_var:
                best_var = var_
                best_bin = b_idx
        print(f"AUTO-DETECT: best_bin={best_bin}, var={best_var:.2f}")
        return best_bin
    else:
        # manual approximate approach
        # we guess from the first item in bin_map[0], e.g. freq_start, freq_step
        # but hackrf_sweep is chunk-based, so let's just pick bin 0 from the big map
        # and see if we find a suitable freq. This is naive.
        # Typically you'd parse each line individually for freq range.
        # We'll just pick the bin that is *closest* to TARGET_FREQ across all data
        best_bin = None
        best_diff = 1e12
        for b_idx, data_list in bin_map.items():
            # look at first item
            if not data_list:
                continue
            # example: data_list[0] = (time, amp_db, freq_start, freq_step)
            freq_s = data_list[0][2]
            freq_stp = data_list[0][3]
            # bin offset is b_idx, but not exactly since we don't know the line offset
            # This is an oversimplification, might not be correct if the CSV lines reorder bins.
            # We do a best guess:
            # freq_x = freq_s + (b_idx * freq_stp) -> Not always correct
            # Instead let's measure amplitude. This is tricky with chunk output.
            # We'll just skip and let the user do real-time approach...
            pass
        # fallback
        return 0

def decode_slow(csv_file):
    bin_map = parse_sweep(csv_file)
    if not bin_map:
        print("No data parsed from CSV.")
        return

    chosen_bin = find_active_bin(bin_map)
    if chosen_bin not in bin_map:
        print(f"Chosen bin {chosen_bin} not in data.")
        return

    # Grab (time, amplitude, freq_start, freq_step) from that bin
    raw_data = bin_map[chosen_bin]
    # Sort by time
    raw_data.sort(key=lambda x: x[0])

    # chunk in intervals of BIT_DURATION
    # We'll track from earliest time to latest
    if not raw_data:
        print("No amplitude points in chosen bin.")
        return

    t_min = raw_data[0][0]
    t_max = raw_data[-1][0]
    # For each chunk (k * BIT_DURATION) to (k+1 * BIT_DURATION),
    # gather amplitude, compute average
    bit_list = []
    current_start = t_min

    idx = 0
    n = len(raw_data)
    chunk_amps = []

    def finalize_chunk(amps):
        if not amps:
            return None
        mean_amp = np.mean(amps)
        return '1' if mean_amp > AMP_THRESHOLD else '0'

    while current_start < t_max:
        chunk_end = current_start + BIT_DURATION
        chunk_pts = []
        while idx < n and raw_data[idx][0] < chunk_end:
            # inside chunk
            val = raw_data[idx][1]
            if not math.isnan(val):
                chunk_pts.append(val)
            idx += 1
        # finalize
        b = finalize_chunk(chunk_pts)
        if b is not None:
            bit_list.append(b)
        current_start += BIT_DURATION + CHUNK_PADDING

    bitstream = ''.join(bit_list)
    print(f"Bitstream read from CSV:\n{bitstream}")

    # If we had a known message length or a known pattern, do more logic
    # e.g. if we expected 4 bits => decode. Or check for repeated patterns
    return bitstream

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <emf_sweep.csv>")
        sys.exit(1)
    csv_path = sys.argv[1]
    bits = decode_slow(csv_path)
    if bits:
        print("Done. Bits:", bits)
    else:
        print("No bits recovered or no data.")
