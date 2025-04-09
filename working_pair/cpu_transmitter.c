cat cpu_transmitter.c 
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <string.h>

#define BITSTREAM "10101"
#define DURATION_ONE 1000000  // microseconds = 0.3s
#define DURATION_ZERO 1000000
#define REPEAT_PAUSE 1000000 // microseconds = 1.0s
#define NUM_THREADS 8        // number of threads to max CPU

volatile int run = 1;

void* burn_cpu(void* arg) {
    while (run) {
        volatile unsigned long long x = 0;
        for (int i = 0; i < 100000; i++) {
            x += i * i;
        }
    }
    return NULL;
}

void start_cpu_load(int microseconds) {
    run = 1;
    pthread_t threads[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_create(&threads[i], NULL, burn_cpu, NULL);
    }

    usleep(microseconds);

    run = 0;

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
}

void transmit_bit(char bit) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    printf("[TX] %02ld:%02ld:%02ld.%03ld BIT=%c\n",
           (ts.tv_sec / 3600) % 24,
           (ts.tv_sec / 60) % 60,
           ts.tv_sec % 60,
           ts.tv_nsec / 1000000,
           bit);
    fflush(stdout);

    if (bit == '1') {
        start_cpu_load(DURATION_ONE);
    } else {
        usleep(DURATION_ZERO);
    }
}

int main() {
    const char* message = BITSTREAM;

    while (1) {
        for (size_t i = 0; i < strlen(message); i++) {
            transmit_bit(message[i]);
        }
        usleep(REPEAT_PAUSE);
    }

    return 0;
}
