hackrf_sweep appears to be not the best match for our goals 

Rather hackrf_transfer can work 


---

hackrf_transfer -f 299000000 -s 10000000 -n 100000000 -r samples_10s.iq



----

Here long_transmitter was running 
and we can see how average changes from 37 to 35 approximately 

 hackrf_transfer -f 299000000 -s 10000000 -n 100000000 -r samples_10s.iq
call hackrf_set_sample_rate(10000000 Hz/10.000 MHz)
call hackrf_set_hw_sync_mode(0)
call hackrf_set_freq(299000000 Hz/299.000 MHz)
samples_to_xfer 100000000/100Mio
Stop with Ctrl-C
19.9 MiB / 1.000 sec = 19.9 MiB/second, average power -37.0 dBfs
19.9 MiB / 1.000 sec = 19.9 MiB/second, average power -37.1 dBfs
19.9 MiB / 1.000 sec = 19.9 MiB/second, average power -37.2 dBfs
20.2 MiB / 1.000 sec = 20.2 MiB/second, average power -37.2 dBfs
19.9 MiB / 1.000 sec = 19.9 MiB/second, average power -37.2 dBfs
19.9 MiB / 1.000 sec = 19.9 MiB/second, average power -37.2 dBfs
20.2 MiB / 1.001 sec = 20.2 MiB/second, average power -36.8 dBfs
19.9 MiB / 0.999 sec = 19.9 MiB/second, average power -35.3 dBfs
19.1 MiB / 1.000 sec = 19.1 MiB/second, average power -35.4 dBfs
19.9 MiB / 1.000 sec = 19.9 MiB/second, average power -35.4 dBfs
 1.0 MiB / 0.043 sec = 24.3 MiB/second, average power -35.3 dBfs

Exiting...
Total time: 10.04325 s
hackrf_stop_rx() done
hackrf_close() done
hackrf_exit() done
fclose() done
exit

----
https://pysdr.org/content/sampling.html
----

pysdr is too heavy for 2GB pi (try on 4GB)
