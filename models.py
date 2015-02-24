import os
import tmdbsimple as tmdb

tmdb.API_KEY = os.environ.get('TMDB_KEY')
app = None


def get_image_url(image, width=500):
    if not image:
        raise IndexError
    image_base_url = "https://image.tmdb.org/t/p/w%d" % width
    return image_base_url + image


class Actor(object):
    def __init__(self, name):
        self.name = name

        person_db = tmdb.Search().person(query=name)
        try:
            self.image = get_image_url(person_db['results'][0]['profile_path'])
        except:
            self.image = ""


class Movie(object):
    def __init__(self, title, year, actors=None):
        self.title = title
        self.year = year
        self.actors = actors

        movie_db = tmdb.Search().movie(query=title, year=year)
        try:
            self.backdrop_image = get_image_url(movie_db['results'][0]['backdrop_path'], 1000)
        except IndexError:
            self.backdrop_image = ""

        try:
            self.poster_image = get_image_url(movie_db['results'][0]['poster_path'], 500)
        except IndexError:
            self.poster_image = ""

    def __str__(self):
        return self.title
