from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import itertools
from threading import Thread
from pytube import Playlist
from functools import lru_cache
import requests
from lib.ExtractDict import extract_dict


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
        elif last_updated_text[0]['text'] == 'Updated ':
            last_updated = datetime.now().date() - timedelta(int(last_updated_text[1]['text']))
        else:
            date_components = last_updated_text[1]['text'].split()
            month = date_components[0]
            day = date_components[1].strip(',')
            year = date_components[2]
            last_updated = datetime.strptime(f"{year}-{month}-{day:0>2}", "%Y-%b-%d").date()
        return last_updated


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
                for s in '\/:*?"<>|': vid_details["title"] = vid_details["title"].replace(s, '')  # Remove illegal chars
                success = True
            except Exception as e:
                print(f'Retrying {vid_url}', e)

        return vid_details["title"], vid_url


    def get_playlist_info(self, url, update_items, update_complete, cache_last_updated=None, first_chunk_size=10, chunk_size=40):
        def get_remaining_playlist_info():
            url_chunk = itertools.islice(urls, first_chunk_size, playlist.length)
            url_info = self.threaded_map(self.get_title, url_chunk, chunk_size)
            update_items({x[0]:x[1] for x in url_info})
            update_complete(playlist.last_updated)


        playlist = FixedPlaylist(url)
        urls = playlist.video_urls

        # Get first 10
        if not cache_last_updated or datetime.strptime(cache_last_updated, "%Y-%m-%d").date() < playlist.last_updated:
            first_url_chunk = itertools.islice(urls, first_chunk_size)
            first_url_info = self.threaded_map(self.get_title, first_url_chunk, first_chunk_size)
            update_items({x[0]:x[1] for x in first_url_info}, True)

            thread = Thread(target=get_remaining_playlist_info)
            thread.start()

            return thread
        
        else:
            print(f'Up to date! Playlist last updated on {str(playlist.last_updated)}')