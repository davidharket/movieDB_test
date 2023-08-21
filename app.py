from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)
app.app_context().push()
API_KEY = "080f54025927bdae154cf0407d3edf68"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

class RateMovieForm(FlaskForm):
    rating = IntegerField(label='rating', validators=[DataRequired()])
    review = StringField(label='review', validators=[DataRequired()])
    submit = SubmitField(label='Done')


class AddMovie(FlaskForm):
    new_movie = StringField(label='movie', validators=[DataRequired()])
    submit = SubmitField(label='Done', validators=[DataRequired()])


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Integer)
    review = db.Column(db.Integer)
    ranking = db.Column(db.String(250))
    img_url = db.Column(db.String(250), unique=True, nullable=False)


db.create_all()


@app.route('/', methods=['GET',  'POST'])
def home():
    all_movies = Movies.query.order_by(Movies.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route('/edit:<title>', methods=['POST', 'GET'])
def edit_movie(title):
    form = RateMovieForm()
    if request.method == 'GET':
        return render_template('edit.html', form=form, title=title)
    else:
        movie_to_update = Movies.query.filter_by(title=title).first()
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        movies = db.session.query(Movies).all()
        return render_template('index.html', movies=movies)


@app.route('/delete:<title>')
def delete_movie(title):
    movie_to_delete = Movies.query.filter_by(title=title).first()
    db.session.delete(movie_to_delete)
    db.session.commit()
    movies = db.session.query(Movies).all()
    return render_template('index.html', movies=movies)


@app.route('/add', methods=['POST', 'GET'])
def add_movie():
    form = AddMovie()
    if form.validate_on_submit():
        movie_title = form.new_movie.data
        response = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}'
                                f'&language=en-US&query={movie_title}&page=1&include_adult=true')
        movie_json = response.json()['results']
        return render_template('select.html', movies=movie_json)
    return render_template('add.html', form=form)


@app.route('/select', methods=['POST', 'GET'])
def select_movie():
    movie_api_id = request.args.get('id')
    movie_api_title = request.args.get('title')
    if movie_api_id:
        movie_api_dict = f'https://api.themoviedb.org/3/search/movie?api_key={API_KEY}'\
                        f'&language=en-US&query={movie_api_title}'
        response = requests.get(movie_api_dict, params={'api_key': API_KEY, 'language': 'en-US'})
        data = response.json()['results']
        for movie in data:
            if movie['id'] == movie_api_id:
                data = movie
        data = data[0]
        print(data['poster_path'])
        new_movie = Movies(
            title=data['original_title'],
            year=data['release_date'].split('-')[0],
            img_url=f'{MOVIE_DB_IMAGE_URL}{data["poster_path"]}',
            description=data['overview']
        )
        db.session.add(new_movie)
        db.session.commit()
        form = RateMovieForm()
        title = data['original_title']
        return render_template('edit.html', form=form, title=title)


if __name__ == '__main__':
    app.run(debug=True)
