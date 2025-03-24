Below is a shorter README for the updated system:

---

```markdown
# RF Sweep Encoder & Decoder

This project simulates an RF transmission system using frequency sweeps. The sender rotates among three sentences, sending transmissions (with clear start/stop markers) interleaved with periods of silence. The receiver reads the sweeps from a CSV, identifies transmissions, and decodes the embedded message.

## Files

- **sender.py**  
  Continuously generates sweeps (each with 1000 points from 300–301 MHz). Transmission sweeps include:
  - **Preamble (rows 100–129)** and **postamble (rows 870–899)**: Markers set to -40 dB.
  - **Message region (rows 130–869)**: Encodes the message bits (-50 dB for '1', -70 dB for '0').
  - Randomized intervals between silence and transmission.
  The sweeps are appended to `sweeps.csv`.

- **decoder.py**  
  Reads `sweeps.csv`, groups sweeps by timestamp, identifies transmissions via the preamble/postamble, and decodes the message from the message region.

- **sweeps.csv**  
  Contains the continuous sweep data with timestamps.

## How to Use

1. **Run the Sender:**  
   ```bash
   python sender.py
   ```
   This will start transmitting and logging sweeps to `sweeps.csv`.

2. **Run the Decoder:**  
   After data collection, run:
   ```bash
   python decoder.py
   ```
   The decoded messages (with their timestamps) will be displayed.

## Requirements

- Python 3.x  
- Packages: `numpy`, `pandas`

Install dependencies with:
```bash
pip install numpy pandas
```

## License

MIT License
```

---

Feel free to adjust any parameters as needed for your application.

