import csv
import gzip
import json
import os


class FileManager(object):
    FILES_FOLDER = "/data"
    CSV_DELIMITER = "|"

    @classmethod
    def write(cls, filename, text, _format=""):
        d = os.path.dirname(filename)
        # First create the directory
        if not os.path.exists(os.path.join(cls.FILES_FOLDER, d)):
            os.makedirs(os.path.join(cls.FILES_FOLDER, d))
        # write into the given file
        o = gzip.open if filename.endswith(".gz") else open
        with o(os.path.join(cls.FILES_FOLDER, filename), "w") as f:
            if _format == "json":
                json.dump(text, f)
            elif _format == "csv":
                writer = csv.writer(f, delimiter=cls.CSV_DELIMITER)
                for line in text:
                    writer.writerow(map(lambda s: s.encode('utf-8') if isinstance(s, unicode) else s, line))
            else:
                f.write(text)

    @classmethod
    def read(cls, filename, _format=""):
        o = gzip.open if filename.endswith(".gz") else open
        with o(os.path.join(cls.FILES_FOLDER, filename), "r") as f:
            if _format == "json":
                return json.load(f)
            elif _format == "csv":
                dict_reader = csv.DictReader(f, delimiter=cls.CSV_DELIMITER)
                cities = []
                first = True
                for row in dict_reader:
                    if first:
                        first = False
                        continue
                    city = {k: v for k, v in row.iteritems() if v}
                    cities.append(city)
                return cities
            else:
                return f.read()

    @classmethod
    def list_files(cls, directory):
        for (_, _, filenames) in os.walk(os.path.join(cls.FILES_FOLDER, directory)):
            return filenames
        return []

    @classmethod
    def exists(cls, filename):
        return os.path.exists(os.path.join(cls.FILES_FOLDER, filename))
