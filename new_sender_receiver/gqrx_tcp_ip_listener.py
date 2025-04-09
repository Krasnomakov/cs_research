import telnetlib
import time
from datetime import datetime

HOST = '127.0.0.1'
PORT = 7356
SAMPLE_INTERVAL = 1.0  # seconds per bit
WINDOW = 10            # moving average window
THRESHOLD_DB = 3.0     # dB above baseline → bit = '1'

def get_power(tn):
    try:
        tn.write(b'l\n')
        response = tn.read_until(b'\n', timeout=1).decode().strip()
        if response.startswith("RPRT") or not response:
            return None
        return float(response)
    except Exception as e:
        print("[ERROR] Failed to read power level:", e)
        return None

def main():
    print(f"[Receiver] Connecting to GQRX via telnet {HOST}:{PORT}...")
    tn = telnetlib.Telnet(HOST, PORT)
    print("[Receiver] Connected.")

    levels = []
    bitstream = ""

    try:
        while True:
            level = get_power(tn)
            now = datetime.now().strftime('%H:%M:%S')

            if level is None:
                print(f"[{now}] No power data")
                time.sleep(SAMPLE_INTERVAL)
                continue

            levels.append(level)
            if len(levels) > WINDOW:
                levels.pop(0)

            baseline = sum(levels) / len(levels)
            delta = level - baseline
            bit = '1' if delta >= THRESHOLD_DB else '0'
            bitstream += bit

            print(f"[{now}] Power: {level:.2f} dB | Δ={delta:+.2f} → {bit}")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\n[Receiver] Stopped. Decoded bitstream:", bitstream)
        tn.close()

if __name__ == "__main__":
    main()
