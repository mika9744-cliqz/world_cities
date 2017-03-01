import datetime
import os
import urllib2
from babel import core as bc
from xml.dom import minidom

from file_manager import FileManager


class OSMXAPI(object):
    URL = "http://overpass.osm.rambler.ru/cgi/xapi_meta"
    CITIES_FOLDER_NAME = "cities"
    PLACE_TYPES = ["city", "town", "village"]
    WORLD_CITIES_FILE = "WORLD_CITIES.json.gz"

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
                if k_attr == "name":
                    city["name"] = tag.getAttribute("v")
                elif k_attr.startswith('name:'):
                    lang_code = k_attr.split(':')[-1]
                    if lang_code:
                        city['names'][lang_code] = tag.getAttribute('v')
                elif k_attr == "population":
                    city["population"] = tag.getAttribute("v")
                elif k_attr == "is_in:country_code":
                    city["country_code"] = tag.getAttribute("v")
                elif k_attr == "is_in:country":
                    city["country"] = tag.getAttribute("v")
            cities.append(city)
        return cities

    @classmethod
    def get_file_name(cls, place_type, min_lon, min_lat, max_lon, max_lat, gz=True):
        now = datetime.datetime.now().strftime("%Y%m%d")
        filename = "%s_%s.json" % (now, '_'.join(map(str, [min_lat, min_lon, max_lat, max_lon])))
        filename = filename + ".gz" if gz else filename
        return os.path.join(cls.CITIES_FOLDER_NAME, place_type, filename)

    @classmethod
    def merge_cities_file(cls, _type="csv"):
        """
        Transform the file for the RH

        :param _type: two possibilities:
                - "csv": merge the extracted cities into a csv file
                - "json": merge the extracted cities into a json file
        :return:
        """
        data = {} if _type == "json" else []
        for place_type in cls.PLACE_TYPES:
            folder = os.path.join(cls.CITIES_FOLDER_NAME, place_type)
            for filename in FileManager.list_files(folder):
                cities = FileManager.read(os.path.join(folder, filename), _json=True)['nodes']
                if _type == "json":
                    data.update(cls.to_json(cities))
                elif _type == "csv":
                    data = cls.to_csv(data, cities)
        if _type == "csv":  # we complete the line with None. We don't have the name ine each language
            l = len(data[0])
            for line in data[1:]:
                for i in range(len(line), l):
                    line.append(None)
        FileManager.write(os.path.join(cls.CITIES_FOLDER_NAME, cls.WORLD_CITIES_FILE), data, _type=_type)

    @classmethod
    def to_csv(cls, data, cities):
        head = ["country_code", "name", "lat", "lon", "population"]
        if len(data) == 0:
            data.append([])
        if len(data[0]) == 0:
            data[0].extend(head)
        for city in cities:
            line = []
            main_name = city.get('name')
            if main_name:
                country_code = city.get("country_code") or cls.get_country_code(city.get("country")) or "ZZ"
                line.extend([country_code, main_name, city.get("lat"), city.get("lon"), city.get("population")])
                for i in range(len(line), len(data[0])):
                    line.append(None)
                for lang, name in city["names"].iteritems():
                    if lang in data[0]:
                        ind = data[0].index(lang)
                        line[ind] = name
                    else:
                        data[0].append(lang)
                        line.append(name)
            data.append(line)
        return data

    @classmethod
    def to_json(cls, cities):
        data = {}
        for city in cities:
            main_name = city.get('name')
            if main_name:
                country_code = city.get("country_code") or cls.get_country_code(city.get("country")) or "ZZ"
                data.setdefault(country_code, {})
                data[country_code][main_name] = dict(
                    lon=city['lon'],
                    lat=city['lat'],
                    population=city.get('population')
                )
                for lang, name in city['names'].iteritems():
                    data[country_code][main_name][lang] = name
        return data

    @classmethod
    def get_country_code(cls, country_name):
        if isinstance(country_name, str):
            loc = bc.Locale("en", "US")
            for country_code, name in loc.territories.iteritems():
                if name.lower() == country_name.lower():
                    return country_code
        return None
