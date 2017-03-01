import datetime
import gzip
import json
import os
import urllib2
from xml.dom import minidom


class OSMXAPI(object):
    URL = "http://overpass.osm.rambler.ru/cgi/xapi_meta"
    CITIES_FOLDER_NAME = "cities"
    PLACE_TYPES = ["city", "town", "village"]
    WORLD_CITIES_FILE = "WORLD_CITIES_CLIQZ.json.gz"

    @classmethod
    def call_api(cls, place_type, min_lon, min_lat, max_lon, max_lat):
        url = "%s?node[place=%s][bbox=%s]" % (cls.URL, place_type, ','.join(map(str, [min_lat, min_lon, max_lat, max_lon])))
        res = urllib2.urlopen(url)
        success, nodes = cls.read_xml(res.read())
        return {"nodes": nodes, "status": "SUCCESS" if success else "FAILED", "url": url}

    @classmethod
    def read_xml(cls, xml):
        dom = minidom.parseString(xml)
        return len(dom.getElementsByTagName("remark")) == 0, cls.extract_nodes(dom.getElementsByTagName('node'))

    @classmethod
    def extract_nodes(cls, nodes):
        cities = []
        for node in nodes:
            city = dict(lon=node.getAttribute('lon'), lat=node.getAttribute('lat'), names={})
            for tag in node.getElementsByTagName('tag'):
                k_attr = tag.getAttribute('k')
                if k_attr.startswith('name:'):
                    country_code = k_attr.split(':')[-1]
                    if country_code:
                        city['names'][country_code] = tag.getAttribute('v')
                if k_attr == "population":
                    city["population"] = tag.getAttribute("v")
            cities.append(city)
        return cities

    @classmethod
    def get_file_name(cls, place_type, min_lon, min_lat, max_lon, max_lat, gz=True):
        now = datetime.datetime.now().strftime("%Y%m%d")
        filename = "%s_%s.json" % (now, '_'.join(map(str, [min_lat, min_lon, max_lat, max_lon])))
        filename = filename + ".gz" if gz else filename
        return os.path.join(cls.CITIES_FOLDER_NAME, place_type, filename)

    @classmethod
    def merge_cities_file(cls):
        """
        Transform the file for the RH

        :return:
        """
        data = {}
        for place_type in cls.PLACE_TYPES:
            folder = os.path.join(cls.CITIES_FOLDER_NAME, place_type)
            for filename in FileManager.list_files(folder):
                cities = FileManager.read(os.path.join(folder, filename), _json=True)['nodes']
                for city in cities:
                    en_name = city['names'].get('en')
                    if en_name:
                        for lang, name in city['names'].iteritems():
                            data.setdefault(lang, {})
                            data[lang][en_name] = dict(
                                name=name,
                                lon=city['lon'],
                                lat=city['lat'],
                                population=city.get('population')
                            )
        FileManager.write(os.path.join(cls.CITIES_FOLDER_NAME, cls.WORLD_CITIES_FILE), data, _json=True)


class FileManager(object):
    FILES_FOLDER = "/data"

    @classmethod
    def write(cls, filename, text, _json=False):
        d = os.path.dirname(filename)
        # First create the directory
        if not os.path.exists(os.path.join(cls.FILES_FOLDER, d)):
            os.makedirs(os.path.join(cls.FILES_FOLDER, d))
        # write into the given file
        o = gzip.open if filename.endswith(".gz") else open
        with o(os.path.join(cls.FILES_FOLDER, filename), "w") as f:
            json.dump(text, f) if _json is True else f.write(text)

    @classmethod
    def read(cls, filename, _json=False):
        o = gzip.open if filename.endswith(".gz") else open
        with o(os.path.join(cls.FILES_FOLDER, filename), "r") as f:
            return json.load(f) if _json is True else f.read()

    @classmethod
    def list_files(cls, directory):
        for (_, _, filenames) in os.walk(os.path.join(cls.FILES_FOLDER, directory)):
            return filenames


class StatsManager(object):
    @classmethod
    def get_osm_extracted_cities_stats(cls):
        stats = {"countries": 0, "cities": 0, "cities_per_country": {}}
        data = FileManager.read(os.path.join(OSMXAPI.CITIES_FOLDER_NAME, OSMXAPI.WORLD_CITIES_FILE), _json=True)
        for lang, cities in data.iteritems():
            stats["countries"] += 1
            stats["cities"]
