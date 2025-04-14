import numpy as np
import time

# Function to perform a RAM-intensive task
def ram_load():
    try:
        # Allocate and modify large arrays repeatedly
        while True:
            # Create a large 2D array with random values
            data = np.random.rand(10000, 10000)  # Adjust size as needed
            # Perform some operations on the array
            data = data * 2 - 1
            # Delay a bit to let the array be held in memory
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    ram_load()

