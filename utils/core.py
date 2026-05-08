import os

from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from musicdl import musicdl
from utils.types import toResponse
import requests
import subprocess

class Core:
    def __init__(self):
        self.lock=False
        home_dir = "./cache"
        self.progress=0
        init_music_clients_cfg = dict()
        init_music_clients_cfg['NeteaseMusicClient'] = {'work_dir': f'{home_dir}/musicdl/Netease'}
        init_music_clients_cfg['QQMusicClient'] = {'work_dir': f'{home_dir}/musicdl/QQ'}
        init_music_clients_cfg['MiguMusicClient'] = {'work_dir': f'{home_dir}/musicdl/migu'}
        init_music_clients_cfg['KuwoMusicClient'] = {'work_dir': f'{home_dir}/musicdl/kuwo'}
        init_music_clients_cfg['QianqianMusicClient'] = {'work_dir': f'{home_dir}/musicdl/qianqian'}

        self.client = musicdl.MusicClient(
            init_music_clients_cfg=init_music_clients_cfg
        )

    def search(self, keyword: str, client: str):
        if not keyword or not client:
            return toResponse(False, "参数不正确")
        self.client.music_sources=[client]
        search_results = self.client.search(keyword)
        local_list = []
        for item in search_results[client]:
            local_list.append({
                "name": item['song_name'],
                "artist": item['singers'],
                "url": item['download_url'],
                "cover": item['cover_url'],
                "album": item['album'],
            })
        return toResponse(True, local_list)
    
    def download_work(self, name: str, artist: str, url: str, cover: str, album: str, quality: str):
        self.progress = 0
        self.lock = True
        try:
            with requests.get(url, stream=True, timeout=15) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                ext = os.path.splitext(url.split('?')[0])[-1] or ".mp3"
                temp_path = f"./cache/temp{ext}"
                final__path = f"./cache/{artist}-{name}.mp3"
                
                downloaded_size = 0
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                self.progress = round((downloaded_size / total_size) * 100, 2)
            
            cmd = [
                "ffmpeg", '-y',
                '-i', temp_path,
                '-i', cover,
                '-map', '0:a',
                '-map', '1:0',
                '-c:a', 'libmp3lame',
                '-b:a', '320k',
                '-metadata', f"title={name}",
                '-metadata', f"artist={artist}",
                '-metadata', f"album={album}",
                '-id3v2_version', '3',
                '-metadata:s:v', 'title=Album cover',
                '-metadata:s:v', 'comment=Cover (front)',
                final__path
            ]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if process.returncode == 0:
                if os.path.exists(final__path):
                    os.remove(temp_path)

        finally:
            self.progress = 0
            self.lock = False
    
    def download(self, name: str, artist: str, url: str, cover: str, album: str, quality: str, background_tasks: BackgroundTasks):
        if not name or not artist or not url or not cover or not album:
            return toResponse(False, "参数不正确")
        if self.lock:
            return toResponse(False, "有任务在进行中")
        
        background_tasks.add_task(self.download_work, name, artist, url, cover, album, quality)

        return toResponse(True, "")
    
    def get_progress(self):
        if self.lock:
            return toResponse(True, self.progress)
        return toResponse(True, "没有在执行的任务")
    
    def get_file(self, name: str, artist: str):
        if not name or not artist:
            return toResponse(False, "参数不正确")
        if self.lock:
            return toResponse(False, "有任务在进行中")
        
        file_path=f"./cache/{artist}-{name}.mp3"
        if not os.path.exists(file_path):
            return toResponse(False, "文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=f"{artist}-{name}.mp3",
            media_type="audio/mpeg"
        )