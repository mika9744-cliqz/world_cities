
import os
from collections import defaultdict

import requests

from file_manager import FileManager


class WikiDataAPI(object):
    endpoint = "https://query.wikidata.org/sparql"
    CITIES_FOLDER_NAME = "wiki_data/cities"
    SUPPORTED_LANGUAGES = ["de", "en", "fr"]
    CSV_HEADER = ["country_code"] + ["name:%s" % lang for lang in SUPPORTED_LANGUAGES]
    WORLD_CITIES_FILE = "WORLD_CITIES.{format}.gz"

    @classmethod
    def request_api(cls, query):
        params = dict(format="json", query=query)
        try:
            res = requests.get(cls.endpoint, params=params, timeout=5).json()
        except:
            res = {}
        return res

    @classmethod
    def format_response(cls, response):
        res = []
        for city in response["results"]["bindings"]:
            city_code = city["city"]["value"].split("/")[-1]
            city_label = city["cityLabel"]["value"] if city["cityLabel"]["value"] != city_code else ""
            res.append({
                "city": city_code,
                "cityLabel": city_label,
                "country": city["country"]["value"].split("/")[-1],
                "countryLabel": city["countryLabel"]["value"],
            })
        return res

    @classmethod
    def get_data(cls, query):
        response = cls.request_api(query)
        if response:
            return cls.format_response(response)
        return []

    @classmethod
    def make_query(cls, country, lang):
        return 'SELECT ?city ?cityLabel ?country ?countryLabel WHERE { ?city (wdt:P31/wdt:P279*) wd:Q515. ?' \
               'city wdt:P17 ?country. SERVICE wikibase:label { bd:serviceParam wikibase:language "%s". } ?' \
               'city wdt:P17 wd:%s.}' % (lang, country)

    @classmethod
    def get_file_name(cls, country, lang, gz=True):
        filename = "cities_%s_%s.json" % (country, lang)
        filename = filename + ".gz" if gz else filename
        return os.path.join(cls.CITIES_FOLDER_NAME, filename)

    @classmethod
    def request_country_codes(cls):
        query = 'SELECT ?country ?countryLabel WHERE {?country wdt:P31 wd:Q6256. ' \
                'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }}'
        res = cls.request_api(query)
        return {
            element[res["head"]["vars"][1]]["value"]: element[res["head"]["vars"][0]]["value"].split('/')[-1]
            for element in res["results"]["bindings"]
        }

    @classmethod
    def to_csv(cls, data, cities, country_code):
        if len(data) == 0:
            data.append(cls.CSV_HEADER)
        for city in cities:
            data.append([country_code, city.get("name:de", ""), city.get("name:en", ""), city.get("name:fr", "")])
        return data

    @classmethod
    def to_json(cls, data, cities, country_code):
        for city in cities:
            data.append([country_code, city.get("name:de", ""), city.get("name:en", ""), city.get("name:fr", "")])
        return data

    @classmethod
    def merge_cities_file(cls, _format="csv"):
        res = []
        for country_code in cls.request_country_codes().iterkeys():
            cities = defaultdict(dict)
            for lang in cls.SUPPORTED_LANGUAGES:
                filename = cls.get_file_name(country_code, lang)
                for element in FileManager.read(filename, _format="json"):
                    cities[element["city"]]['name:%s' % lang] = element["cityLabel"]
            if _format == "json":
                res = cls.to_json(res, cities.itervalues(), country_code)
            elif _format == "csv":
                res = cls.to_csv(res, cities.itervalues(), country_code)
            else:
                raise TypeError("Format %s not supported" % _format)
        FileManager.write(os.path.join(cls.CITIES_FOLDER_NAME, cls.WORLD_CITIES_FILE.format(format=_format)),
                          res, _format=_format)

    @classmethod
    def has_already_data(cls, country, lang):
        filename = cls.get_file_name(country, lang)
        if FileManager.exists(filename):
            return True
