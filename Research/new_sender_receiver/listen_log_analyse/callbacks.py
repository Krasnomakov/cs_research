def my_callback(hackrf_transfer):
    c = hackrf_transfer.contents
    values = cast(c.buffer, POINTER(c_byte*c.buffer_length)).contents
    iq = bytes2iq(bytearray(values))

    return 0


# Start receiving...
hackrf.start_rx(my_callback)

# If you want to stop receiving...
hackrf.stop_rx()
