import math
import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.ticker as ticker
import time

PATH = os.path.dirname(os.path.realpath(__file__))


def lerp_chunks(data_chunks, scale=2):
    new_data_chunks = np.zeros(((data_chunks.shape[0]-1)*scale+1, data_chunks.shape[1]), dtype=np.float32)

    for i in range(0, len(data_chunks)-1):
        new_data_chunks[i*scale] = data_chunks[i]
        scale_unit = (data_chunks[i+1]-data_chunks[i])/scale

        for j in range(1, scale):
            new_data_chunks[i*scale+j] = data_chunks[i] + scale_unit*j

    new_data_chunks[-1] = data_chunks[-1]

    return new_data_chunks


def band_split(data_chunks, freq_ax, freq_pows=(5,14), band_count=12, avg=False):
    freq_bands = 2 ** np.linspace(freq_pows[0], freq_pows[1], band_count, dtype=np.float32)
    freq_points = np.zeros(len(freq_bands), dtype=np.uint16)
    data_bands = np.zeros((len(data_chunks), len(freq_points)), dtype=np.float32)

    ax_index = 0
    for i, band in enumerate(freq_bands):
        while freq_ax[ax_index] < band:
            ax_index += 1

        freq_points[i] = ax_index
    
    if avg:
        for i, data in enumerate(data_chunks):
            data_bands[i][0] = data[:freq_points[0]].sum()/len(data[:freq_points[0]])
            for j in range(1, len(freq_points)):
                data_bands[i][j] = data[freq_points[j-1]:freq_points[j]].sum()/len(data[freq_points[j-1]:freq_points[j]])
    else:
        for i, data in enumerate(data_chunks):
            data_bands[i][0] = data[:freq_points[0]].sum()
            for j in range(1, len(freq_points)):
                data_bands[i][j] = data[freq_points[j-1]:freq_points[j]].sum()

    return freq_bands, data_bands


def update(i):
    global time_elapsed, prev_time
    # timer = time.perf_counter()
    visual_line.set_ydata(data_chunks[i])
    stft_line.set_ydata(data_bands_stft[1][i])
    fmt_line.set_ydata(data_bands_fmt[1][i])
    cqt_line.set_ydata(data_bands_cqt[1][i])

    current_time = time.perf_counter()
    time_diff = current_time - prev_time
    time_elapsed += time_diff
    prev_time = current_time
    if i%200 == 199:
        print(f'AVG FPS: {i/time_elapsed}')
    # print(time.perf_counter()-timer)
    return visual_line, stft_line, fmt_line, cqt_line


audio_path = f'{PATH}/audio/ヴァンパイア - 尾丸ポルカ(cover).opus'
# audio_path = f'{PATH}/audio/400 Hz Test Tone.opus'
data, sr = librosa.load(audio_path, sr=None)

chunk_size = 2048  # sr//fps
lerp_scale = 2
fps = sr*lerp_scale/chunk_size
chunk_count = len(data)//chunk_size+1
time_length = len(data)/sr
time_scale = 1/fps
ft_index = chunk_size
mel_index = ft_index//8
bin_index = 114

data_chunks = np.zeros((chunk_count, chunk_size), np.float32)
for i in range(1, chunk_count-1):
    data_chunks[i] = data[chunk_size*(i):chunk_size*(i+1)]
data_chunks[-1] = np.resize(data_chunks, chunk_size)
data_chunks = lerp_chunks(data_chunks, scale=lerp_scale)

chunk_time_ax = [i/sr for i in range(chunk_size)]

# # RealTime
# # data_chunks_stft = np.zeros((len(data_chunks), ft_index//2+1), np.float32)
# # max_stft = 0
# # for i, x in enumerate(data_chunks):
# #     stft = np.abs(librosa.stft(x, n_fft=ft_index, hop_length=chunk_size*2, center=False))

# #     stft_arr = np.zeros(len(stft), np.float32)
# #     for j, y in enumerate(stft):
# #         stft_arr[j] = y[0]
# #         if y[0] > max_stft:
# #             max_stft = y[0]
# #     data_chunks_stft[i] = stft_arr

# # RealTime (also probably wrong)
# # data_chunks_fmt = np.zeros((chunk_count, ft_index//2+1), np.float32)
# # for i, x in enumerate(data_chunks):
# #     data_chunks_fmt[i] = np.abs(librosa.fmt(x, n_fmt=ft_index))
# # max_fmt = np.max(data_chunks_fmt)

data_chunks_stft = np.abs(librosa.stft(data, n_fft=ft_index, hop_length=ft_index, center=False))
data_chunks_stft = np.transpose(data_chunks_stft, (1,0))
data_chunks_stft = np.resize(data_chunks_stft, (chunk_count, ft_index//2+1))
data_chunks_stft[-1] = np.zeros(ft_index//2+1, np.float32)
data_chunks_stft = lerp_chunks(data_chunks_stft, scale=lerp_scale)
max_stft = np.amax(data_chunks_stft)
stft_freq_ax = librosa.fft_frequencies(sr=sr, n_fft=ft_index)
data_bands_stft = band_split(data_chunks_stft, stft_freq_ax, band_count=12)

data_chunks_fmt = librosa.feature.melspectrogram(y=data, n_fft=ft_index, hop_length=ft_index, center=False, n_mels=mel_index, sr=sr)
data_chunks_fmt = np.transpose(data_chunks_fmt, (1,0))
data_chunks_fmt = np.resize(data_chunks_fmt, (chunk_count, mel_index))
data_chunks_fmt[-1] = np.zeros(mel_index, np.float32)
data_chunks_fmt = lerp_chunks(data_chunks_fmt, scale=lerp_scale)
max_fmt = np.amax(data_chunks_fmt)
fmt_freq_ax = librosa.mel_frequencies(n_mels=mel_index, fmax=sr/2)
data_bands_fmt = band_split(data_chunks_fmt, fmt_freq_ax, band_count=16)

data_chunks_cqt = np.abs(librosa.cqt(data, n_bins=bin_index, hop_length=ft_index, fmin=32, sr=sr))
data_chunks_cqt = np.transpose(data_chunks_cqt, (1,0))
data_chunks_cqt = lerp_chunks(data_chunks_cqt, scale=lerp_scale)
max_cqt = np.amax(data_chunks_cqt)
cqt_freq_ax = librosa.cqt_frequencies(n_bins=bin_index, fmin=32)
data_bands_cqt = band_split(data_chunks_cqt, cqt_freq_ax, band_count=40)

fig, ax = plt.subplots(4, 1, figsize=(4, 6), gridspec_kw={'height_ratios': [1, 1, 1, 1]})
fig.suptitle(f'XMV {fps}FPS {time_length}s')

ax[0].set_title('Visualizer')
ax[0].set(
    xlabel='Time',
    ylabel='Amplitude',
    ylim=(min(data), max(data)),
    xlim=(0, chunk_time_ax[-1])
)
visual_line, = ax[0].plot(chunk_time_ax, data_chunks[0])

ax[1].set_title('STFT')
ax[1].set_xscale('log', base=2)
ax[1].xaxis.set_major_formatter(ticker.ScalarFormatter())
ax[1].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, np.amax(data_bands_stft[1])),
    xlim=(32, 16384),
    yscale='symlog',
)
stft_line, = ax[1].step(data_bands_stft[0], data_bands_stft[1][0])

ax[2].set_title('FMT')
ax[2].set_xscale('log', base=2)
ax[2].xaxis.set_major_formatter(ticker.ScalarFormatter())
ax[2].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, np.amax(data_bands_fmt[1])),  
    xlim=(32, 16384),
    yscale='symlog',
)
fmt_line, = ax[2].step(data_bands_fmt[0], data_bands_fmt[1][0])

ax[3].set_title('CQT')
ax[3].set_xscale('log', base=2)
ax[3].xaxis.set_major_formatter(ticker.ScalarFormatter())
ax[3].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, np.amax(data_bands_cqt[1])),
    xlim=(32, 16384),
    yscale='symlog',
)
cqt_line, = ax[3].step(data_bands_cqt[0], data_bands_cqt[1][0])

time_elapsed = 0
prev_time = time.perf_counter()
anim = FuncAnimation(fig, update, blit=True, interval=time_scale*150, frames=chunk_count*lerp_scale, repeat=False, save_count=chunk_count)  # interval = time_scale*1000
# anim.save(f'{PATH}/test.mp4', writer='imagemagick', fps=fps)

plt.tight_layout()
plt.show()
