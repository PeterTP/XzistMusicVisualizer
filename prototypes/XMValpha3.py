import math
import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

PATH = os.path.dirname(os.path.realpath(__file__))


def update(i):
    global time_elapsed, prev_time
    # timer = time.perf_counter()
    visual_line.set_ydata(data_chunks[i])
    stft_line.set_ydata(data_chunks_stft[i])
    fmt_line.set_ydata(data_chunks_fmt[i])
    cqt_line.set_ydata(data_chunks_cqt[i])

    current_time = time.perf_counter()
    time_elapsed += current_time - prev_time
    prev_time = current_time
    if i%100 == 99:
        print(f'AVG FPS: {i/time_elapsed}')
    # print(time.perf_counter()-timer)
    return visual_line, stft_line, fmt_line, cqt_line


audio_path = f'{PATH}/audio/ヴァンパイア - 尾丸ポルカ(cover).opus'
# audio_path = f'{PATH}/audio/400 Hz Test Tone.opus'
data, sr = librosa.load(audio_path, sr=None)

chunk_size = 1024  # sr//fps
fps = sr/chunk_size
chunk_count = len(data)//chunk_size+1
time_length = len(data)/sr
time_scale = chunk_size/sr
ft_index = chunk_size
mel_index = ft_index//8
bin_index = 114

data_chunks = np.zeros((chunk_count, chunk_size), np.float32)
for i in range(1, chunk_count-1):
    data_chunks[i] = data[chunk_size*(i):chunk_size*(i+1)]
data_chunks[-1] = np.resize(data_chunks, chunk_size)

chunk_time_ax = [i/sr for i in range(chunk_size)]

# RealTime
# data_chunks_stft = np.zeros((len(data_chunks), ft_index//2+1), np.float32)
# max_stft = 0
# for i, x in enumerate(data_chunks):
#     stft = np.abs(librosa.stft(x, n_fft=ft_index, hop_length=chunk_size*2, center=False))

#     stft_arr = np.zeros(len(stft), np.float32)
#     for j, y in enumerate(stft):
#         stft_arr[j] = y[0]
#         if y[0] > max_stft:
#             max_stft = y[0]
#     data_chunks_stft[i] = stft_arr

# RealTime (also probably wrong)
# data_chunks_fmt = np.zeros((chunk_count, ft_index//2+1), np.float32)
# for i, x in enumerate(data_chunks):
#     data_chunks_fmt[i] = np.abs(librosa.fmt(x, n_fmt=ft_index))
# max_fmt = np.max(data_chunks_fmt)

data_chunks_stft = np.abs(librosa.stft(data, n_fft=ft_index, hop_length=ft_index, center=False))
data_chunks_stft = np.transpose(data_chunks_stft, (1,0))
data_chunks_stft = np.resize(data_chunks_stft, (chunk_count, ft_index//2+1))
data_chunks_stft[-1] = np.zeros(ft_index//2+1, np.float32)
max_stft = np.amax(data_chunks_stft)
stft_freq_ax = librosa.fft_frequencies(sr=sr, n_fft=ft_index)

data_chunks_fmt = librosa.feature.melspectrogram(y=data, n_fft=ft_index, hop_length=ft_index, center=False, n_mels=mel_index, sr=sr)
data_chunks_fmt = np.transpose(data_chunks_fmt, (1,0))
data_chunks_fmt = np.resize(data_chunks_fmt, (chunk_count, mel_index))
data_chunks_fmt[-1] = np.zeros(mel_index, np.float32)
max_fmt = np.amax(data_chunks_fmt)
fmt_freq_ax = librosa.mel_frequencies(n_mels=mel_index, fmax=sr/2)

data_chunks_cqt = np.abs(librosa.cqt(data, n_bins=bin_index, hop_length=ft_index, fmin=32, sr=sr))
data_chunks_cqt = np.transpose(data_chunks_cqt, (1,0))
max_cqt = np.amax(data_chunks_cqt)
cqt_freq_ax = librosa.cqt_frequencies(n_bins=bin_index, fmin=32)

fig, ax = plt.subplots(4, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [1, 1, 1, 1]})
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
ax[1].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, max_stft),
    xlim=(32, stft_freq_ax[-1]),
    yscale='symlog',
)
stft_line, = ax[1].plot(stft_freq_ax, data_chunks_stft[0])

ax[2].set_title('FMT')
ax[2].set_xscale('log', base=2)
ax[2].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, max_fmt),  
    xlim=(32, fmt_freq_ax[-1]),
    yscale='symlog',
)
fmt_line, = ax[2].plot(fmt_freq_ax, data_chunks_fmt[0])

ax[3].set_title('CQT')
ax[3].set_xscale('log', base=2)
ax[3].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(0, max_cqt),
    xlim=(32, fmt_freq_ax[-1]),
    yscale='symlog',
)
cqt_line, = ax[3].plot(cqt_freq_ax, data_chunks_cqt[0])

time_elapsed = 0
prev_time = time.perf_counter()
anim = FuncAnimation(fig, update, blit=True, interval=time_scale*200*(chunk_size/1024), frames=chunk_count, repeat=False, save_count=chunk_count)  # interval = time_scale*1000
# anim.save(f'{PATH}/test.mp4', writer='imagemagick', fps=fps)

plt.tight_layout()
plt.show()
