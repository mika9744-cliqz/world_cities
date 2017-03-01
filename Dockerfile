FROM python:2.7

MAINTAINER <mickael@cliqz.com>

LABEL version="0.1"

VOLUME ["/data"]

ENV PYTHONUNBUFFERED=0

RUN pip install docopt

WORKDIR /workspace

COPY ./scripts .

ENTRYPOINT ["python", "extract_world_cities.py"]

CMD python extract_world_cities.py
