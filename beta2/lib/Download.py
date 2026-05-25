from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue
from yt_dlp import YoutubeDL
from lib.GetPlaylistInfo import GetPlaylistInfo
# import soundfile as sf
# import pyloudnorm as pyln


class Download:
    def __init__(self, PATH):
        self.PATH = PATH

        self.queue = Queue()
        self.active = False
        self.ydl_opts = {
            'format': 'bestaudio[ext=webm]',
            'concurrent_fragment_downloads': 4,
            'ignoreerrors': True,
            # 'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192'
            }]
        }


    def threaded_map(self, func, params, max_workers=40):
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            return [x for x in pool.map(func, params)]


    def process_audio(self, data):
        while True:
            try:
                opts = {x: self.ydl_opts[x] for x in self.ydl_opts}
                opts['outtmpl'] = f'{str(self.location)}/{data["name"]}.%(ext)s'
                with YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(data['url'])  # Downloads audio (yep this function downloads the audio too despite its name)

                # Normalize audio loudness
                # file_path = f"{str(self.PATH)}/tmp/{self.name}.opus"
                # data, sr = sf.read(file_path)
                # meter = pyln.Meter(sr)
                # loudness = meter.integrated_loudness(data)
                # loudness_normalized_audio = pyln.normalize.loudness(data, loudness, -14.0)
                # sf.write(file_path, loudness_normalized_audio, sr, format='ogg', subtype='opus')

                return info

            except Exception as e:
                print(f'Retrying download', e)


    def process_downloads(self):
        self.active = True

        while not self.queue.empty():
            self.process_audio(self.queue.get())
        
        self.active = False


    def download_audios(self, audio_infos, location=None, prioritise=False):
        if location:
            self.location = location
        else:
            self.location = self.PATH/'tmp'/'audio'

        if prioritise:
            # Clear queue
            while not self.queue.empty():
                self.queue.get()

        for data in audio_infos:
            self.queue.put(data)

        if not self.active:
            self.audio_process = Process(target=self.process_downloads)
            self.audio_process.start()

        return self.audio_process


    def process_batch_downloads(self):
        def update_items(info, set=False):
            if set:
                data_dict.clear()

            data_dict.update(info)


        def update_complete(_):
            pass


        data_dict = {}
        thread = GetPlaylistInfo().get_playlist_info(self.playlist_url, update_items, update_complete)
        thread.join()
        data_arr = [{'name': x, 'url': data_dict[x]} for x in data_dict]
        self.threaded_map(self.process_audio, data_arr, 16)


    def batch_download_audios(self, playlist_url, location):
        self.playlist_url = playlist_url
        self.location = location

        # Doing this makes this function work concurrently even if another function is still
        self.audio_process = Process(target=self.process_batch_downloads)
        self.audio_process.start()

        return self.audio_process