import numpy as np
import librosa
import time
import os

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


audio_path = f'{PATH}/audio/ヴァンパイア - 尾丸ポルカ(cover).opus'
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

start_time = time.perf_counter()

data_chunks_stft = np.abs(librosa.stft(data, n_fft=ft_index, hop_length=ft_index, center=False))
data_chunks_stft = np.transpose(data_chunks_stft, (1,0))
data_chunks_stft = np.resize(data_chunks_stft, (chunk_count, ft_index//2+1))
data_chunks_stft[-1] = np.zeros(ft_index//2+1, np.float32)
# data_chunks_stft = lerp_chunks(data_chunks_stft, scale=lerp_scale)
max_stft = np.amax(data_chunks_stft)
stft_freq_ax = librosa.fft_frequencies(sr=sr, n_fft=ft_index)
# data_bands_stft = band_split(data_chunks_stft, stft_freq_ax, band_count=12)
end_time = time.perf_counter()
print(end_time-start_time)
start_time = end_time

data_chunks_fmt = librosa.feature.melspectrogram(y=data, n_fft=ft_index, hop_length=ft_index, center=False, n_mels=mel_index, sr=sr)
data_chunks_fmt = np.transpose(data_chunks_fmt, (1,0))
data_chunks_fmt = np.resize(data_chunks_fmt, (chunk_count, mel_index))
data_chunks_fmt[-1] = np.zeros(mel_index, np.float32)
# data_chunks_fmt = lerp_chunks(data_chunks_fmt, scale=lerp_scale)
max_fmt = np.amax(data_chunks_fmt)
fmt_freq_ax = librosa.mel_frequencies(n_mels=mel_index, fmax=sr/2)
# data_bands_fmt = band_split(data_chunks_fmt, fmt_freq_ax, band_count=16)
end_time = time.perf_counter()
print(end_time-start_time)
start_time = end_time

data_chunks_cqt = np.abs(librosa.cqt(data, n_bins=bin_index, hop_length=ft_index, fmin=32, sr=sr))
data_chunks_cqt = np.transpose(data_chunks_cqt, (1,0))
# data_chunks_cqt = lerp_chunks(data_chunks_cqt, scale=lerp_scale)
max_cqt = np.amax(data_chunks_cqt)
cqt_freq_ax = librosa.cqt_frequencies(n_bins=bin_index, fmin=32)
# data_bands_cqt = band_split(data_chunks_cqt, cqt_freq_ax, band_count=40)
end_time = time.perf_counter()
print(end_time-start_time)
start_time = end_time