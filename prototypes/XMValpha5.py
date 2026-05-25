import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker
import time
import sounddevice as sd
import soundfile as sf

PATH = os.path.dirname(os.path.realpath(__file__))


def band_split(data, freq_ax, freq_pows=(5,14), band_count=12, avg=False):
    freq_bands = 2 ** np.linspace(freq_pows[0], freq_pows[1], band_count, dtype=np.float32)
    freq_points = np.zeros(len(freq_bands), dtype=np.uint16)
    data_bands = np.zeros(len(data), dtype=np.float32)

    ax_index = 0
    for i, band in np.ndenumerate(freq_bands):
        while freq_ax[ax_index] < band:
            ax_index += 1

        freq_points[i] = ax_index
    
    if avg:
        data_bands[0] = data[:freq_points[0]].sum()/len(data[:freq_points[0]])
        for j in range(1, len(freq_points)):
            data_bands[j] = data[freq_points[j-1]:freq_points[j]].sum()/len(data[freq_points[j-1]:freq_points[j]])
    else:
        data_bands[0] = data[:freq_points[0]].sum()
        for j in range(1, len(freq_points)):
            data_bands[j] = data[freq_points[j-1]:freq_points[j]].sum()

    return freq_bands, data_bands


def set_data(indata):
    global data, data_stft, data_fmt, data_cqt
    data = np.array((indata[:,0] + indata[:,1])/2, dtype='float32')
    data_stft = np.abs(librosa.stft(data, n_fft=ft_index, hop_length=ft_index*2, center=False)).flatten()
    data_fmt = librosa.feature.melspectrogram(y=data, n_fft=ft_index, hop_length=ft_index, center=False, n_mels=mel_index, sr=sr).flatten()
    # data_cqt = np.abs(librosa.cqt(data, n_bins=bin_index, hop_length=ft_index, fmin=32, sr=sr)).flatten()


count = 0
def callback(indata, outdata, frames, time, status):
    global count, is_read_file

    total_data = np.zeros((chunk_size, indata.shape[1]), dtype=np.float32)
    
    if is_read_file:
        
        if count >= chunk_count:
            is_read_file = False
            return

        outdata[:chunk_size] = data_chunks[count]  # interesting I can't set it directly but i have to add [:chunk_size] 
        count += 1

        total_data += data_chunks[count]

    if is_use_mic:
        total_data += indata #np.maximum(total_data, indata)
        
    set_data(total_data)


def update(i):
    global time_elapsed, prev_time, data, data_stft, data_fmt, data_cqt

    # data_band_stft = band_split(data_stft, stft_freq_ax, band_count=12)
    # data_band_fmt = band_split(data_fmt, fmt_freq_ax, band_count=16)
    # data_band_cqt = band_split(data_cqt, cqt_freq_ax, band_count=40)

    visual_line.set_ydata(data)
    stft_line.set_ydata(data_stft)
    fmt_line.set_ydata(data_fmt)
    # cqt_line.set_ydata(data_cqt)

    # data /= 1.01
    # data_stft /= 1.1
    # data_fmt /= 1.1
    # data_cqt /= 1.1

    current_time = time.perf_counter()
    time_diff = current_time - prev_time
    time_elapsed += time_diff
    prev_time = current_time
    if i%200 == 199:
        print(f'AVG FPS: {i/time_elapsed}')

    return visual_line, stft_line, fmt_line, cqt_line


sr = 48000
chunk_size = 2048  # sr//fps
ft_index = chunk_size
mel_index = ft_index//8
bin_index = 114

data_ax = [i/sr for i in range(chunk_size)]
freq_ax = 2 ** np.linspace(5, 14, 10, dtype=np.float32)
stft_freq_ax = librosa.fft_frequencies(sr=sr, n_fft=ft_index)
fmt_freq_ax = librosa.mel_frequencies(n_mels=mel_index, fmax=sr/2)
cqt_freq_ax = librosa.cqt_frequencies(n_bins=bin_index, fmin=32)

data = np.zeros(chunk_size, np.float32)
data_stft = np.zeros(len(stft_freq_ax), np.float32)
data_fmt = np.zeros(len(fmt_freq_ax), np.float32)
data_cqt = np.zeros(len(cqt_freq_ax), np.float32)

is_read_file = True
is_use_mic = False
if is_read_file:
    file_path = f'{PATH}/audio/ヴァンパイア - 尾丸ポルカ(cover).opus'
    file_data, sr = sf.read(file_path, dtype='float32')
    chunk_count = len(file_data)//chunk_size+1
    
    data_chunks = np.zeros((chunk_count, chunk_size, file_data.shape[1]), np.float32)
    for i in range(0, chunk_count-1):
        data_chunks[i] = file_data[chunk_size*(i):chunk_size*(i+1)]
    data_chunks[-1] = np.resize(file_data[chunk_size*(chunk_count-1):], (chunk_size, file_data.shape[1]))

fps = sr/chunk_size
time_scale = 1/fps


fig, ax = plt.subplots(4, 1, figsize=(6, 6), gridspec_kw={'height_ratios': [1, 1, 1, 1]})
fig.suptitle(f'XMV {fps}FPS')

ax[0].set_title('Visualizer')
ax[0].set(
    xlabel='Time',
    ylabel='Amplitude',
    ylim=(-1.2,1.2),
    xlim=(0, data_ax[-1])
)
visual_line, = ax[0].plot(data_ax, data)

ax[1].set_title('STFT')
ax[1].set_xscale('log', base=2)
ax[1].xaxis.set_major_formatter(ticker.ScalarFormatter())
ax[1].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, 2000),
    xlim=(32, 16384),
    yscale='symlog',
)
stft_line, = ax[1].plot(stft_freq_ax, data_stft)

ax[2].set_title('FMT')
ax[2].set_xscale('log', base=2)
ax[2].xaxis.set_major_formatter(ticker.ScalarFormatter())
ax[2].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, 20000),
    xlim=(32, 16384),
    yscale='symlog',
)
fmt_line, = ax[2].plot(fmt_freq_ax, data_fmt)

ax[3].set_title('CQT')
ax[3].set_xscale('log', base=2)
ax[3].xaxis.set_major_formatter(ticker.ScalarFormatter())
ax[3].set(
    ylabel='Amplitude',
    # xlabel='Frequency',
    ylim=(0, 50),
    xlim=(32, 16384),
    yscale='symlog',
)
cqt_line, = ax[3].plot(cqt_freq_ax, data_cqt)

time_elapsed = 0
prev_time = time.perf_counter()
ani = FuncAnimation(fig, update, blit=True, interval=0, repeat=False)  # interval = time_scale*1000
# ani.save(f'{PATH}/test.mp4', writer='imagemagick', fps=fps)

plt.tight_layout()

stream = sd.Stream(samplerate=sr, blocksize=chunk_size, dtype=np.float32, channels=2, callback=callback, latency=0)

with stream:
    plt.show()
