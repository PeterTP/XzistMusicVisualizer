import os
import librosa
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib import animation
import matplotlib.pyplot as plt
import time

PATH = os.path.dirname(os.path.realpath(__file__))


def update(i):
    # t1 = time.perf_counter()
    line.set_ydata(data_chunks[i])
    line2.set_height(data_chunks_std[i])
    line3.set_height(data_chunks_max[i])
    line4.set_height(data_chunks_avg[i])
    line5.set_ydata(data_chunks_stft[i])
    # librosa.display.specshow(data_chunks_stft[i], x_axis='time', y_axis='log', sr=sr, ax=ax[1][0])
    # print(time.perf_counter() - t1)
    return line, line2, line3, line4, line5


audio_path = f'{PATH}/audio/ヴァンパイア - 尾丸ポルカ(cover).opus'
# audio_path = f'{PATH}/audio/400 Hz Test Tone.opus'
data, sr = librosa.load(audio_path, sr=None)
#chunk_size = 4096
chunk_size = int(sr/60)
data_arr = np.array(data, np.float16)
chunk_count = int(len(data_arr)/chunk_size)+1
data_chunks = np.zeros((chunk_count, chunk_size), np.float16)

for i in range(1, chunk_count-1):
    data_chunks[i] = data_arr[chunk_size*(i):chunk_size*(i+1)]
data_chunks[-1] = np.resize(data_chunks, chunk_size)

data_chunks_std = [np.std(x) for x in data_chunks]
data_chunks_std = np.array(data_chunks_std, np.float16)
data_chunks_max = [max(x) for x in data_chunks]
data_chunks_max = np.array(data_chunks_max, np.float16)
data_chunks_avg = [np.average(x) for x in data_chunks]
data_chunks_avg = np.array(data_chunks_avg, np.float16)

data_chunks_stft = np.zeros((data_chunks.size, int(512/2+1)), np.float16)
min_stft = 0
max_stft = 0
for i, x in enumerate(data_chunks):
    stft = np.abs(librosa.stft(x, n_fft=512, hop_length=chunk_size*2))
    
    stft_arr = np.zeros(stft.size, np.float16)
    for j, y in enumerate(stft):
        stft_arr[j] = y[0]
        if y[0] > max_stft:
            max_stft = y[0]
        elif y[0] < max_stft:
            min_stft = y[0]
    data_chunks_stft[i] = stft_arr

print(data_chunks_stft.shape, min_stft, max_stft)


time_scale = chunk_size/sr
fps = 1/time_scale
time_length = len(data)/sr

fig, ax = plt.subplots(2, 4, figsize=(14, 4), gridspec_kw={'width_ratios': [6, 1, 1, 1]})
fig.suptitle(f'XMV {fps}FPS {time_length}s')

ax[0][0].set_title('Visualizer')
ax[0][0].set(
    xlabel='Time',
    ylabel='Amplitude',
    ylim=(min(data_arr), max(data_arr)),
    xlim=(0, chunk_size)
)
line, = ax[0][0].plot(data_chunks[0])

ax[0][1].set_title('Std. Deviation')
ax[0][1].set(
    ylim=(min(data_chunks_std), max(data_chunks_std)),
    xlim=(0, 1)
)
line2, = ax[0][1].bar(0.5, data_chunks_std[0])

ax[0][2].set_title('Max Amp.')
ax[0][2].set(
    ylim=(min(data_chunks_max), max(data_chunks_max)),
    xlim=(0, 1)
)
line3, = ax[0][2].bar(0.5, data_chunks_max[0])

ax[0][3].set_title('Avg Amp.')
ax[0][3].set(
    ylim=(min(data_chunks_avg), max(data_chunks_avg)),
    xlim=(0, 1)
)
line4, = ax[0][3].bar(0.5, data_chunks_avg[0])

ax[1][0].set_title('STFT')
ax[1][0].set(
    ylabel='Amplitude',
    xlabel='Frequency',
    ylim=(min_stft, max_stft),
    xlim=(0, int(512/2+1)),
    yscale='symlog'
)
line5, = ax[1][0].plot(data_chunks_stft[0])


anim = FuncAnimation(fig, update, interval=(10*time_scale), blit=True, save_count=chunk_count)
# anim.save(f'{PATH}/test.mp4', writer='imagemagick', fps=fps)




# librosa.display.specshow(data_chunks_stft[1000], x_axis='time', y_axis='log', sr=sr, ax=ax[1][0])
plt.tight_layout()
plt.show()
