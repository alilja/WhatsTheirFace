import re
import os
from operator import itemgetter

from rottentomatoes import RT
from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.contrib.cache import SimpleCache

import search_utils
import models

# setup flask
app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = 7200  # two hours

models.app = app

cache = SimpleCache()


@app.route('/')
def index():
    placeholder = ""
    if "movie" in session:
        placeholder = session['movie']
    else:
        top_rental = cache.get('top_rental')
        if not placeholder:
            top_rentals_rt = RT().lists('dvds', 'top_rentals')
            top_rental = models.Movie(
                top_rentals_rt['movies'][0]['title'],
                top_rentals_rt['movies'][0]['year'],
            )
            cache.set('top_rental', top_rental, timeout=60 * 60 * 24)
            placeholder = top_rental
    return render_template("index.html", first_placeholder=placeholder)


@app.route('/results/', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        movies = []
        for field_name in request.form:
            search_string = request.form.get(field_name)
            if not search_string:
                if field_name == "movie_one":
                    # if the search string is blank, check to see if we have one
                    # stored in the session cookie
                    if "movie" in session:
                        search_string = session["movie"]
                    else:
                        top_rental = cache.get('top_rental')
                        if not top_rental:
                            return render_template("empty_error.html", movie_name="")
                        else:
                            search_string = top_rental.title
                else:
                    return render_template("empty_error.html", movie_name="")

            try:
                movie = find_movie(search_string)
            except MovieNotFound as not_found:
                return render_template("error.html", movie_name=not_found.args[0])

            if field_name == "movie_one":
                session['movie'] = movie.title
            movies.append(movie)

        common_actors = []
        for actor in list(set(movies[0].actors) & set(movies[1].actors)):
            common_actors.append(models.Actor(actor))

        six_column = []
        i = 0
        temp = []
        for actor in common_actors:
            if i == 6:
                six_column.append(temp)
                temp = []
                i = 0
            temp.append(actor)
            i += 1
        six_column.append(temp)

        return render_template(
            "results.html",
            current_movie=movies[0],
            other_movie=movies[1],
            common_actors=six_column,
        )
    return redirect(url_for('index'))


class MovieNotFound(Exception):
    pass


def find_movie(text):
    info_regex = re.search(
        r"(?P<name>[a-zA-Z0-9 '\".,/:;#!$%&-+=_<>?]+) ?(?:\((?P<year>\d{4})\))?",
        text
    )
    name = info_regex.group('name')
    year = info_regex.group('year')

    # 1. search
    try:
        results = RT().search(name)
    except:
        raise MovieNotFound(name)

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
    if not movies:
        raise MovieNotFound(name)

    # 3. figure out which movie we're talking about
    this_movie = None
    if year is None:
        this_movie = max(movies, key=itemgetter(u'year'))
    else:
        try:
            this_movie = (movie for movie in movies if movie['year'] == int(year)).next()
        except:
            raise MovieNotFound(name)

    # 4. get cast
    movie_id = int(this_movie['id'])

    return models.Movie(
        this_movie['title'],
        this_movie['year'],
        [actor['name'] for actor in RT().info(movie_id, 'cast')['cast']],
    )


if __name__ == '__main__':
    app.run(debug=True)
