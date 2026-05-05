from musicdl import musicdl
from utils.types import toResponse

class Core:
    def __init__(self):
        self.lock=False
        home_dir = "./cache"
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