import os
import tmdbsimple as tmdb

tmdb.API_KEY = os.environ.get('TMDB_KEY')


class Actor(object):
    image_base_url = "https://image.tmdb.org/t/p/w500"

    def __init__(self, name):
        self.name = name

        person_db = tmdb.Search().person(query=name)
        self.image = Actor.image_base_url + person_db['results'][0]['profile_path']


class Movie(object):
    def __init__(self, title, year, actors):
        self.title = title
        self.year = year
        self.actors = actors