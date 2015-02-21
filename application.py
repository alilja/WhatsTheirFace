import re
from operator import itemgetter

from rottentomatoes import RT
from flask import Flask, render_template, redirect, url_for, request, session

import search_utils

app = Flask(__name__)
app.secret_key = "sadjkada"


""" Right now I'm watching [           ], and
    I think this actor was also in [        ] """


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['movie_one'] = request.form['movie_one'] # this should be saved within a 2-3 hour period and then cleared
        session['movie_two'] = request.form['movie_two'] # this should always be empty
        return redirect(url_for('results'))
    return render_template("index.html")


@app.route('/results/')
def results():
    if 'movie_one' in session and 'movie_two' in session:
        movie_one = find_movie(session['movie_one'])
        movie_two = find_movie(session['movie_two'])
        common_actors = list(set(movie_one[2]) & set(movie_two[2]))
        return str(common_actors)
    return redirect(url_for('index')) # this should remember your previous searches and display them


class MovieNotFound(Exception):
    pass


def find_movie(text):
    info_regex = re.search(
        (r"(?P<name>[a-zA-Z0-9 '\".,/:;#!$%&-+=_<>?]+)"
         r" *(?:\((?P<year>\d{4})\))?"),
        text
    )
    name = info_regex.group('name')
    year = info_regex.group('year')

    # 1. search
    try:
        results = RT().search(name)
    except:
        raise MovieNotFound

    # 2. find the movies with the closest title similarities
    highest_rank = 0
    movies = []
    for movie in results:
        # Simon White's algorithim, implemented here:
        # http://stackoverflow.com/questions/653157/a-better-similarity-ranking-algorithm-for-variable-length-strings
        if movie['title'].lower() == name.lower():
            movies = [movie]
            break

        rank = search_utils.string_similarity(name, movie['title'])
        if rank >= highest_rank:
            movies.append(movie)
            highest_rank = rank

    # 3. figure out which movie we're talking about
    this_movie = None
    if year is None:
        this_movie = max(movies, key=itemgetter(u'year'))
    else:
        try:
            this_movie = (movie for movie in movies if movie['year'] == int(year)).next()
        except:
            raise MovieNotFound

    # 4. get cast
    movie_id = int(this_movie['id'])

    return (
        this_movie['title'],
        this_movie['year'],
        [actor['name'] for actor in RT().info(movie_id, 'cast')['cast']],
    )

if __name__ == '__main__':
    app.run(debug=True)
