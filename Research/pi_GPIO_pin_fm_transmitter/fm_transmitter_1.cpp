#include "transmitter.hpp"
#include <iostream>
#include <csignal>
#include <unistd.h>

std::mutex mtx;
bool enable = true;
Transmitter *transmitter = nullptr;

// Signal handler for stopping the transmitter
void sigIntHandler(int sigNum)
{
    if (transmitter) {
        std::cout << "Signal received: " << sigNum << ". Stopping transmitter..." << std::endl;
        transmitter->Stop();
        enable = false;
    }
}

int main(int argc, char** argv)
{
    float frequency = 100.f, bandwidth = 200.f;
    uint16_t dmaChannel = 0;
    bool showUsage = true, loop = false;
    int opt, filesOffset;

    // Parse command-line arguments
    while ((opt = getopt(argc, argv, "rf:d:b:v")) != -1) {
        switch (opt) {
            case 'r':
                loop = true;
                break;
            case 'f':
                frequency = std::stof(optarg);
                std::cout << "Frequency set to: " << frequency << " MHz" << std::endl;
                break;
            case 'd':
                dmaChannel = std::stoi(optarg);
                std::cout << "DMA Channel set to: " << dmaChannel << std::endl;
                break;
            case 'b':
                bandwidth = std::stof(optarg);
                std::cout << "Bandwidth set to: " << bandwidth << " kHz" << std::endl;
                break;
            case 'v':
                std::cout << "Program version: 1.0" << std::endl;
                return 0;
        }
    }

    if (optind < argc) {
        filesOffset = optind;
        showUsage = false;
    }
    if (showUsage) {
        std::cout << "Usage: fm_transmitter [-f <frequency>] [-b <bandwidth>] [-d <dma_channel>] [-r] <file>" << std::endl;
        return 0;
    }

    int result = EXIT_SUCCESS;

    // Signal handling for clean exit
    std::signal(SIGINT, sigIntHandler);
    std::signal(SIGTERM, sigIntHandler);

    try {
        transmitter = new Transmitter();
        std::cout << "Broadcasting at " << frequency << " MHz with " << bandwidth << " kHz bandwidth" << std::endl;

        // Loop through audio files
        do {
            std::string filename = argv[optind++];
            if ((optind == argc) && loop) {
                optind = filesOffset;
            }
            std::cout << "Loading file: " << filename << std::endl;
            WaveReader reader(filename != "-" ? filename : std::string(), enable, mtx);
            WaveHeader header = reader.GetHeader();
            std::cout << "Playing: " << reader.GetFilename() << ", "
                      << header.sampleRate << " Hz, "
                      << header.bitsPerSample << " bits, "
                      << ((header.channels > 1) ? "stereo" : "mono") << std::endl;

            transmitter->Transmit(reader, frequency, bandwidth, dmaChannel, optind < argc);
        } while (enable && (optind < argc));
    } catch (std::exception &e) {
        std::cout << "Error: " << e.what() << std::endl;
        result = EXIT_FAILURE;
    }

    if (transmitter) {
        delete transmitter;
        transmitter = nullptr;
    }

    return result;
}
