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

cache = SimpleCache()


@app.route('/')
def index():
    placeholder = ""
    if "movie" in session:
        placeholder = session['movie']
    else:
        placeholder = cache.get('top_rental')
        if not placeholder:
            top_rentals = RT().lists('dvds', 'top_rentals')
            placeholder = top_rentals['movies'][0]['title']
            cache.set('top_rental', placeholder, timeout=60 * 60 * 24)
    return render_template("index.html", first_placeholder=placeholder)


@app.route('/results/', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        movies = []
        for field_name in request.form:
            search_string = request.form.get(field_name)
            if not search_string:
                # if the search string is blank, check to see if we have one
                # stored in the session cookie
                if "movie" in session:
                    search_string = session["movie"]
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

        return render_template(
            "results.html",
            current_name=movies[0].title,
            current_date=movies[0].year,
            other_name=movies[1].title,
            other_date=movies[1].year,
            common_actors=common_actors,
        )
    return redirect(url_for('index'))  # this should remember your previous searches and display them


class MovieNotFound(Exception):
    pass


def find_movie(text):
    info_regex = re.search(
        r"(?P<name>[a-zA-Z0-9 '\".,/:;#!$%&-+=_<>?]+) ?(?:\((?P<year>\d{4})\))?",
        text
    )
    name = info_regex.group('name')
    year = info_regex.group('year')
    app.logger.debug(name)
    app.logger.debug(year)

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
