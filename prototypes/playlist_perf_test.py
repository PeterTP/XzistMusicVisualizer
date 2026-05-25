from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, timedelta
import json
from pytube import Playlist, YouTube
from functools import lru_cache
import itertools
import requests
import time
from threading import Thread
from pyx.ExtractDict import extract_dict
import asyncio


# def show_time(start_time):
#     end_time = time.perf_counter()
#     print(end_time-start_time)


# def threaded_map(func, params, max_workers=40):
#     with ThreadPoolExecutor(max_workers=max_workers) as pool:
#         return [x for x in pool.map(func, params)]


# def extract_dict(text, key):
#     result = ''
#     index = text.index('"' + key + '"') + len(key) + 3

#     while True:
#         if text[index] == '{':
#             break

#         index += 1
    
#     bracket_count = 0
#     quotation_count = 0
#     while True:
#         char = text[index]
#         result += char

#         if char == '\\':
#             index += 1
#             char = text[index]
#             result += char
#         elif char == '{':
#             bracket_count += 1
#         elif char == '}' and quotation_count % 2 == 0:
#             bracket_count -= 1
#         elif char == '"':
#             quotation_count += 1

#         if bracket_count < 1:
#             break

#         index += 1

#     return json.loads(result)


# def extract_dict2(text, key):
#     start_index = text.index('"' + key + '"') + len(key) + 3

#     while True:
#         if text[start_index] == '{':
#             break

#         start_index += 1
    
#     end_index = start_index
#     bracket_count = 0
#     quotation_count = 0
#     while True:
#         char = text[end_index]

#         if char == '\\':
#             end_index += 1
#             char = text[end_index]
#         elif char == '{':
#             bracket_count += 1
#         elif char == '}' and quotation_count % 2 == 0:
#             bracket_count -= 1
#         elif char == '"':
#             quotation_count += 1

#         if bracket_count < 1:
#             break

#         end_index += 1

#     result = text[start_index:end_index+1]
#     return json.loads(result)


# def get_title(vid_url):
#     success = False
#     while not success:
#         try:
#             text = requests.get(vid_url).text
#             vid_details = extract_dict(text, "videoDetails")
#             success = True
#         except:
#             print('Retrying', vid_url)
#             success = False
#             time.sleep(0.1)
    
#     return vid_details["title"], vid_url


# def get_title2(vid_url):
#     return YouTube(vid_url).title, vid_url


# def get_title_alt(vid):
#     return vid.title, vid.watch_url



url = 'https://www.youtube.com/playlist?list=PLvGjOmDNpIGgFiVcBisFKkZkMHdGiV9wh'  # PLuJl1cYYdUxi7lZGXqUYoBT-SOsRtS6Je

# same playlist test https://www.youtube.com/playlist?list=PLjp0AEEJ0-fGKG_3skl0e1FQlJfnx-TJz
# start_time = time.perf_counter()
# vid_urls = scrapetube.get_playlist('PLvGjOmDNpIGgFiVcBisFKkZkMHdGiV9wh')
# a = [x["videoId"] for x in vid_urls]
# vid_titles = threaded_map(get_title, a)
# # print(vid_titles)
# show_time(start_time)

# start_time = time.perf_counter()
# vid_urls = pytube.Playlist(url).video_urls
# vid_titles = []
# get_title(vid_urls[0])
# # for i in range(0, 1000000):
# #     data_chunk = itertools.islice(vid_urls, 40*i, 40*(i+1))
# #     vid_titles += threaded_map(get_title, data_chunk)
# #     show_time(start_time)
# show_time(start_time)

# start_time = time.perf_counter()
# print(start_time)
# vids = pytube.Playlist(url).length
# print(vids)
# # vid_titles = []
# # data_chunk = itertools.islice(vids, 0, 10)
# # vid_titles += threaded_map(get_title_alt, data_chunk)
# show_time(start_time)
# # for i in range(0, 1000000):
# #     data_chunk = itertools.islice(vids, 80*i+10, 80*(i+1)+10)
# #     vid_titles += threaded_map(get_title_alt, data_chunk)
# #     show_time(start_time)
# # show_time(start_time)



# start_time = time.perf_counter()
# print('Clcik')
# playlist = pytube.Playlist(url)
# vids = playlist.videos

# vid_chunk_1 = itertools.islice(vids, 10)
# vid_info = threaded_map(get_title_alt, vid_chunk_1, 10)
# show_time(start_time)

# playlist_length = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['stats'][0]['runs'][0]['text']
# playlist_length = playlist_length.replace(',','')
# if playlist_length == 'No videos':
#     playlist_length = 0
# elif playlist_length == '1 video':
#     playlist_length = 1
# playlist_length = int(playlist_length)

# start_time = time.perf_counter()
# vid_chunk_2 = itertools.islice(vids, 10, playlist_length)
# vid_info += threaded_map(get_title_alt, vid_chunk_2)

# vid_info_dict = {x[0]:x[1] for x in vid_info}
    

# show_time(start_time)

# def get_playlist_info2(first_chunk_size=10, chunk_size=40):
#     stat = time.perf_counter()
#     def get_remaining_playlist_info():
#         playlist_length = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['stats'][0]['runs'][0]['text']
#         playlist_length = playlist_length.replace(',','')
#         if playlist_length == 'No videos':
#             playlist_length = 0
#         elif playlist_length == '1 video':
#             playlist_length = 1
#         playlist_length = int(playlist_length)

#         playlist_chunk_2 = itertools.islice(playlist, first_chunk_size, playlist_length)
#         playlist_info_2 = threaded_map(get_title, playlist_chunk_2, chunk_size)
#         info.update({x[0]:x[1] for x in playlist_info_2})
#         print(info)

#         # chunk_count = playlist_length//chunk_size+1
#         # for i in range(0, chunk_count-1):
#         #     playlist_chunk = itertools.islice(playlist, chunk_size*i, chunk_size*(i+1))
#         #     playlist_info = threaded_map(get_title, playlist_chunk)
#         #     info.update({x[0]:x[1] for x in playlist_info})
#         #     print(info)

#         # playlist_chunk = itertools.islice(playlist, chunk_count-1, playlist_length)
#         # playlist_info = threaded_map(get_title, playlist_chunk)
#         # info.update({x[0]:x[1] for x in playlist_info})
#         # print(info)

#         print(time.perf_counter() - stat)


#     playlist = Playlist(url)
#     last_updated_text = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['stats'][2]['runs']
#     if last_updated_text[0]['text'] == 'Updated today':
#         last_updated = datetime.now().date()
#     elif last_updated_text[0]['text'] == 'Updated yesterday':
#         last_updated = datetime.now().date() - timedelta(1)
#     else:
#         date_components = last_updated_text[1]['text'].split()
#         month = date_components[0]
#         day = date_components[1].strip(',')
#         year = date_components[2]
#         last_updated = datetime(year, month, day).date()
    
#     first_playlist_chunk = itertools.islice(playlist, first_chunk_size)
#     first_playlist_info = threaded_map(get_title, first_playlist_chunk, first_chunk_size)
#     remaining_playlist_thread = Thread(target=get_remaining_playlist_info)
#     remaining_playlist_thread.start()

#     return {x[0]:x[1] for x in first_playlist_info}, remaining_playlist_thread


# def get_playlist_info(first_chunk_size=10):
#     def get_remaining_playlist_info():
#         playlist_length = playlist.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['stats'][0]['runs'][0]['text']
#         playlist_length = playlist_length.replace(',','')
#         if playlist_length == 'No videos':
#             playlist_length = 0
#         elif playlist_length == '1 video':
#             playlist_length = 1
#         playlist_length = int(playlist_length)

#         playlist_chunk_2 = itertools.islice(vids, first_chunk_size, playlist_length)
        
#         playlist_info_2 = threaded_map(get_title_alt, playlist_chunk_2)
#         info.update({x[0]:x[1] for x in playlist_info_2})
#         print(info)


#     playlist = pytube.Playlist(url)
#     vids = playlist.videos

#     playlist_chunk_1 = itertools.islice(vids, first_chunk_size)
#     playlist_info = threaded_map(get_title_alt, playlist_chunk_1)
#     remaining_playlist_thread = Thread(target=get_remaining_playlist_info)
#     remaining_playlist_thread.start()

#     return {x[0]:x[1] for x in playlist_info}, remaining_playlist_thread


class FixedPlaylist(Playlist):
    def __init__(self, url):
        super().__init__(url)

 
    @property
    @lru_cache
    def length(self):
        playlist_length = self.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['stats'][0]['runs'][0]['text']
        playlist_length = playlist_length.replace(',','')

        if playlist_length == 'No videos':
            playlist_length = 0
        elif playlist_length == '1 video':
            playlist_length = 1

        return int(playlist_length)


    @property
    @lru_cache
    def last_updated(self):
        last_updated_text = self.sidebar_info[0]['playlistSidebarPrimaryInfoRenderer']['stats'][2]['runs']
        if last_updated_text[0]['text'] == 'Updated today':
            last_updated = datetime.now().date()
        elif last_updated_text[0]['text'] == 'Updated yesterday':
            last_updated = datetime.now().date() - timedelta(1)
        else:
            date_components = last_updated_text[1]['text'].split()
            month = date_components[0]
            day = date_components[1].strip(',')
            year = date_components[2]
            last_updated = datetime.strptime(f"{year}-{month}-{day:0>2}", "%Y-%b-%d").date()
        return last_updated


# class GetPlaylistInfo:
#     def threaded_map(self, func, params, max_workers=40):
#         with ThreadPoolExecutor(max_workers=max_workers) as pool:
#             return [x for x in pool.map(func, params)]
    

#     def get_title(self, vid_url):
#         success = False
#         while not success:
#             try:
#                 text = requests.get(vid_url).text
#                 vid_details = extract_dict(text, "videoDetails")
#                 success = True
#             except Exception as e:
#                 print(e)
        
#         return vid_details["title"], vid_url


#     async def async_map(self, func, params):
#         tasks = [asyncio.ensure_future(func(x)) for x in params]
#         return await asyncio.gather(*tasks)


#     async def get_request(self,url):
#         return requests.get(url)


#     def async_get_title(self, vid_urls):
#         success = False
#         urls = list(vid_urls)

#         while not success:
#             try:
#                 response = asyncio.run(self.async_map(self.get_request, urls))
#                 vid_details = []
#                 for x in response:
#                     vid_details.append(extract_dict(x.text, "videoDetails"))
#                 success = True
#             except Exception as e:
#                 print(e)
        
#         result = {}
#         for i, url in enumerate(urls):
#             result[vid_details[i]['title']] = url
#         return result


#     def get_playlist_info(self, url, cache_last_updated, set_items, set_last_update, first_chunk_size=10, subchunk_size=4):
#         def get_remaining_playlist_info():
#             subchunk_count = (playlist.length - first_chunk_size)//subchunk_size + 1
#             subchunks = []
#             for i in range(0, subchunk_count-1):
#                 subchunks.append(itertools.islice(playlist, subchunk_size*i, subchunk_size*(i+1)))
#             subchunks.append(itertools.islice(playlist, subchunk_count-1, playlist.length))

#             url_info = self.threaded_map(self.async_get_title, subchunks)
#             for info_dict in url_info: set_items(info_dict)
#             set_last_update(playlist.last_updated)
        

#         playlist = FixedPlaylist(url)
#         urls = playlist.video_urls
#         # Get first 10
#         if datetime.strptime(cache_last_updated, "%Y-%m-%d").date() < playlist.last_updated:
#             first_url_chunk = itertools.islice(urls, first_chunk_size)
#             first_url_info = self.threaded_map(self.get_title, first_url_chunk, first_chunk_size)
#             set_items({x[0]:x[1] for x in first_url_info})

#             thread = Thread(target=get_remaining_playlist_info)
#             thread.start()

#             return thread


class GetPlaylistInfo:
    def threaded_map(self, func, params, max_workers=40):
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            return [x for x in pool.map(func, params)]


    def get_title(self, vid_url):
        success = False
        while not success:
            try:
                text = requests.get(vid_url).text
                vid_details = extract_dict(text, "videoDetails")
                success = True
            except:
                print('Retrying', vid_url)
        
        return vid_details["title"], vid_url


    def get_playlist_info(self, url, cache_last_updated, set_items, set_last_update, first_chunk_size=10, chunk_size=40):
        def get_remaining_playlist_info():
            url_chunk = itertools.islice(urls, first_chunk_size, playlist.length)
            url_info = self.threaded_map(self.get_title, url_chunk, chunk_size)
            set_items({x[0]:x[1] for x in url_info})
            set_last_update(playlist.last_updated)
        

        playlist = FixedPlaylist(url)
        urls = playlist.video_urls
        # Get first 10
        if datetime.strptime(cache_last_updated, "%Y-%m-%d").date() < playlist.last_updated:
            first_url_chunk = itertools.islice(urls, first_chunk_size)
            first_url_info = self.threaded_map(self.get_title, first_url_chunk, first_chunk_size)
            set_items({x[0]:x[1] for x in first_url_info})

            thread = Thread(target=get_remaining_playlist_info)
            thread.start()

            return thread


# class GetPlaylistInfo:
#     def threaded_map(self, func, params, max_workers=40):
#         with ThreadPoolExecutor(max_workers=max_workers) as pool:
#             return [x for x in pool.map(func, params)]


#     def get_title(self, vid_resp):
#         success = False
#         while not success:
#             try:
#                 text = vid_resp.text
#                 vid_details = extract_dict(text, "videoDetails")
#                 success = True
#             except Exception as e:
#                 print(e)
        
#         return vid_details["title"], f'https://www.youtube.com/watch?v={vid_details["videoId"]}'


#     async def async_map(self, func, params):
#         tasks = [asyncio.ensure_future(func(x)) for x in params]
#         return await asyncio.gather(*tasks)


#     async def get_request(self,url):
#         return requests.get(url)


#     def get_playlist_info(self, url, cache_last_updated, set_items, set_last_update, first_chunk_size=10, chunk_size=40):
#         def get_remaining_playlist_info():
#             url_chunk = itertools.islice(urls, first_chunk_size, playlist.length)
#             url_info = self.threaded_map(self.get_title, url_chunk, chunk_size)
#             set_items({x[0]:x[1] for x in url_info})
#             set_last_update(playlist.last_updated)
        

#         playlist = FixedPlaylist(url)
#         urls = playlist.video_urls
#         # Get first 10
#         if datetime.strptime(cache_last_updated, "%Y-%m-%d").date() < playlist.last_updated:
#             first_url_chunk = itertools.islice(urls, first_chunk_size)
#             first_response = asyncio.run(self.async_map(self.get_request, first_url_chunk))
#             first_url_info = self.threaded_map(self.get_title, first_response, first_chunk_size)
#             set_items({x[0]:x[1] for x in first_url_info})

#             thread = Thread(target=get_remaining_playlist_info)
#             # thread.start()

#             return thread
        

stat = time.perf_counter()


def set_items(a):
    info.update(a)
    print(info)
    print(time.perf_counter() - stat)


def set_last_update(date):
    pass


info = {}
def run():
    GetPlaylistInfo().get_playlist_info(url, '2020-2-2', set_items, set_last_update)

    while True:
        pass
run()

# #Target = "YOASOBI「アイドル」 Official Music Video", unwanted = "Idol"
# with open('a.txt', 'w', encoding='utf-8') as f:
#     f.write(requests.get('https://youtube.com/watch?v=ZRtdQ81jPUQ').text)
