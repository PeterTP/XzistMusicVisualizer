import os
import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
# import time

PATH = os.path.dirname(os.path.realpath(__file__))


def update(i):
    # timer = time.perf_counter()
    visual_line.set_ydata(data_chunks[i])
    ft_line.set_ydata(data_chunks_stft[i])
    # print(time.perf_counter()-timer)
    return visual_line, ft_line


audio_path = f'{PATH}/audio/ヴァンパイア - 尾丸ポルカ(cover).opus'
data, sr = librosa.load(audio_path, sr=None)

chunk_size = 4096  # int(sr/fps)
fps = int(sr/chunk_size)
chunk_count = int(len(data)/chunk_size)+1
time_length = len(data)/sr
time_scale = chunk_size/sr

data_chunks = np.zeros((chunk_count, chunk_size), np.float32)
for i in range(1, chunk_count-1):
    data_chunks[i] = data[chunk_size*(i):chunk_size*(i+1)]
data_chunks[-1] = np.resize(data_chunks, chunk_size)

chunk_time_ax = [i/sr for i in range(chunk_size)]

n_fft = chunk_size


# RealTime
# data_chunks_stft = np.zeros((len(data_chunks), int(n_fft/2+1)), np.float32)
# max_stft = 0
# for i, x in enumerate(data_chunks):
#     stft = np.abs(librosa.stft(x, n_fft=n_fft, hop_length=chunk_size*2, center=False))

#     stft_arr = np.zeros(len(stft), np.float32)
#     for j, y in enumerate(stft):
#         stft_arr[j] = y[0]
#         if y[0] > max_stft:
#             max_stft = y[0]
#     data_chunks_stft[i] = stft_arr


data_chunks_stft = np.abs(librosa.stft(data, n_fft=n_fft, hop_length=n_fft, center=False))
data_chunks_stft = np.transpose(data_chunks_stft, (1,0))
data_chunks_stft = np.resize(data_chunks_stft, (chunk_count, int(n_fft/2)+1))
data_chunks_stft[-1] = np.zeros(int(n_fft/2)+1, np.float32)
max_stft = np.amax(data_chunks_stft)
stft_time_ax = librosa.fft_frequencies(sr=sr, n_fft=n_fft)


fig, ax = plt.subplots(2, 1, figsize=(12, 6), gridspec_kw={'height_ratios': [1, 3]})
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
    xlim=(16, max(stft_time_ax)),
    yscale='symlog',
)
ft_line, = ax[1].plot(stft_time_ax, data_chunks_stft[0])


anim = FuncAnimation(fig, update, blit=True, interval=0, frames=chunk_count, repeat=False, save_count=chunk_count)  # interval = time_scale*1000
# anim.save(f'{PATH}/test.mp4', writer='imagemagick', fps=fps)


plt.tight_layout()
plt.show()
