import os

from file_manager import FileManager
from osm_xapi import OSMXAPI


class StatsManager(object):
    @classmethod
    def get_osm_extracted_cities_stats(cls):
        stats = {"countries": 0, "cities": 0, "cities_per_country": {}}
        data = FileManager.read(os.path.join(OSMXAPI.CITIES_FOLDER_NAME, OSMXAPI.WORLD_CITIES_FILE), _json=True)
        for lang, cities in data.iteritems():
            stats["countries"] += 1
