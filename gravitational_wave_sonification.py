import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt


def normalize(data):
    return (data - np.min(data)) / (np.max(data) - np.min(data))


def repeat_data(data, num_repeats):
    repeated_data = np.tile(data, (num_repeats, 1))
    return repeated_data


def apply_bandpass_filter(data, sample_rate, low_freq, high_freq):
    nyquist_freq = 0.5 * sample_rate
    low_cutoff = low_freq / nyquist_freq
    high_cutoff = high_freq / nyquist_freq
    sos = butter(10, [low_cutoff, high_cutoff], btype='band', output='sos')

    # Apply the filter to each channel independently
    filtered_data = np.apply_along_axis(lambda x: sosfilt(sos, x), 1, data)

    return filtered_data


def convert_to_sound(data, duration_factor=1, sample_rate=44100, output_filename='gravitational_wave_audio.wav'):
    num_channels, data_length = data.shape

    # Normalize and scale the data for each channel independently
    scaled_data = np.zeros(data.shape)
    for channel in range(num_channels):
        scaled_data[channel] = 2 * (normalize(data[channel]) - 0.5)  # Scale the data to range [-1, 1]

    # Repeat the data to increase the audio duration
    num_repeats = int(duration_factor)
    repeated_data = repeat_data(scaled_data, num_repeats)

    # Apply a window function (Hann window) to each channel
    window = np.hanning(data_length)
    windowed_data = repeated_data * window

    # Perform Fourier transform for each channel
    freq_data = np.fft.fft(windowed_data)

    # Calculate the frequency range for the given sample rate and data length
    freq_range = np.fft.fftfreq(data_length, d=1.0 / sample_rate)
    freq_range = freq_range[:data_length // 2]  # Use only positive frequencies

    # Apply a logarithmic scale to the frequency range with a small constant added to prevent zero values
    small_constant = 1e-10
    log_freq_range = np.logspace(np.log10(freq_range[1]), np.log10(freq_range[-1]), data_length // 2) + small_constant

    # Apply a bandpass filter to select relevant frequency range (adjust these values as needed)
    low_freq = 10.0  # Minimum frequency (Hz)
    high_freq = 1000.0  # Maximum frequency (Hz)
    # can also use the hardcoded frequency ranges instead of log_freq
    filtered_freq_data = apply_bandpass_filter(freq_data, sample_rate, log_freq_range[0], log_freq_range[-1])

    # Convert back to the time domain using inverse Fourier transform
    processed_data = np.fft.ifft(filtered_freq_data, axis=1).real

    # Scale the data to fit within the audible range (-1 to 1) for each channel
    processed_data = (processed_data - np.min(processed_data)) / (np.max(processed_data) - np.min(processed_data))
    processed_data = 2 * (processed_data - 0.5)

    # Convert the processed data to 16-bit PCM audio format for each channel
    scaled_data = (processed_data * 32767).astype(np.int16)

    # Create stereo WAV file with each channel representing different detectors
    stereo_wav_data = np.column_stack((scaled_data[0], scaled_data[1]))

    # Save the audio to a stereo WAV file
    wavfile.write(output_filename, sample_rate, stereo_wav_data)

    # Plot the spectrogram of the sonified data
    plt.figure()
    plt.specgram(stereo_wav_data[:, 0], Fs=sample_rate, cmap='viridis')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Spectrogram of Gravitational Wave Sonification')
    plt.colorbar(label='Intensity (dB)')
    plt.savefig('spectrogram.png')
    plt.show()


if __name__ == "__main__":
    # Load the gravitational wave data from the npy file
    gw_data = np.load('sep_data.npy', allow_pickle=True)
    h1 = np.concatenate([gw_data[0], gw_data[3]])
    l1 = np.concatenate([gw_data[1], gw_data[2]])

    plt.figure()
    plt.plot(h1, label="H1")
    plt.plot(l1, label="L1")
    plt.legend(loc="upper right")
    plt.savefig('wave_plot.png')
    plt.show()

    gw_data = np.vstack([h1, l1])

    duration_factor = 1

    # Convert the gravitational wave data to sound for each channel
    convert_to_sound(gw_data, duration_factor, output_filename='gravity.wav')
