from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os


API_KEY = os.environ["API_KEY"]
TOKEN = os.environ["TOKEN"]
MOVIES_ENDPOINT = "https://api.themoviedb.org/3/search/movie"

header = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json;charset=utf-8'"
}

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top_movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap(app)

db = SQLAlchemy(app)


class EditForm(FlaskForm):
    new_rating = StringField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired(message="This field can't be empty")])
    new_review = StringField("Your Review", validators=[DataRequired(message="This field can't be empty")])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    new_title = StringField("Movie Title", validators=[DataRequired(message="This field can't be empty")])
    submit = SubmitField('Add Movie')


with app.app_context():

    class Movie(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(250), unique=True, nullable=False)
        year = db.Column(db.Integer, nullable=False)
        description = db.Column(db.String(250), nullable=False)
        rating = db.Column(db.Float, nullable=False)
        ranking = db.Column(db.Integer, nullable=False)
        review = db.Column(db.String(250), nullable=False)
        img_url = db.Column(db.String(250), nullable=False)

    db.create_all()

    # db.session.add(new_movie)
    # db.session.commit()

    @app.route("/")
    def home():
        all_movies = Movie.query.order_by(Movie.rating).all()
        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies)-i
        db.session.commit()
        return render_template("index.html", movies=all_movies)


    @app.route("/edit", methods=['GET', 'POST'])
    def edit():
        form = EditForm()
        movie_id = request.args.get("id")
        movie_to_update = Movie.query.get(movie_id)

        if request.method == "POST":
            movie_to_update.rating = request.form['new_rating']
            movie_to_update.review = request.form['new_review']
            db.session.commit()
            return redirect(url_for('home'))

        return render_template("edit.html", movie=movie_to_update, form=form)


    @app.route("/delete")
    def delete():
        movie_id = request.args.get("id")
        movie_to_delete = Movie.query.get(movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for("home"))


    @app.route("/add", methods=["GET", "POST"])
    def add():
        add_form = AddForm()
        if request.method == "POST":
            data = str(request.form["new_title"])
            query = {
                "api_key": API_KEY,
                "query": data,
            }
            respond = requests.get(url=MOVIES_ENDPOINT, params=query, headers=header)
            movies_data = respond.json()["results"]
            return render_template("select.html", movies=movies_data)
        return render_template("add.html", form=add_form)

    @app.route("/find", methods=["GET", "POST"])
    def find():
        search_movie_id = request.args.get("id")
        new_url = f"https://api.themoviedb.org/3/movie/{search_movie_id}"
        query = {
            "api_key": API_KEY,
        }
        search_respond = requests.get(new_url, params=query, headers=header)
        movie_details = search_respond.json()
        print(movie_details)
        new_movie = Movie(
            title=movie_details["original_title"],
            year=movie_details["release_date"].split("-")[0],
            description=movie_details["overview"],
            rating=0,
            ranking=10,
            review="PASS",
            img_url=f"https://image.tmdb.org/t/p/w300{movie_details['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        find_movie = Movie.query.filter_by(title=movie_details["original_title"]).first()
        movie_id = find_movie.id
        return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
