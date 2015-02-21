import os
import tmdbsimple as tmdb

tmdb.API_KEY = os.environ.get('TMDB_KEY')
app = None


def get_url(image, width=500):
    image_base_url = "https://image.tmdb.org/t/p/w%d" % width
    return image_base_url + image


class Actor(object):
    def __init__(self, name):
        self.name = name

        person_db = tmdb.Search().person(query=name)
        self.image = get_url(person_db['results'][0]['profile_path'])


class Movie(object):
    def __init__(self, title, year, actors):
        self.title = title
        self.year = year
        self.actors = actors

        movie_db = tmdb.Search().movie(query=title, year=year)
        self.backdrop_image = get_url(movie_db['results'][0]['backdrop_path'], 1024)
        self.backdrop_image = get_url(movie_db['results'][0]['poster_path'], 500)
