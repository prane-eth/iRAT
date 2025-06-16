import simple_cache
import os
from irat.utils.settings import Settings

class Cache(object):
    def __init__(self, filename: str, folder: str = None, ttl: int = None):
        self.folder = folder or Settings.get('CACHE_FOLDER')
        self.filename = os.path.join(self.folder, filename)
        self.ttl = ttl or int(Settings.get('CACHE_DEFAULT_TTL'))

    def get(self, key: str):
        return simple_cache.load_key(self.filename, key)

    def set(self, key: str, value: any):
        return simple_cache.save_key(self.filename, key, value, self.ttl)
    
    def prune(self):
        simple_cache.prune_cache(self.filename)
