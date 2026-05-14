import math
import os
from functools import wraps
from urllib.parse import urlsplit

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_

from extensions import db
from models import Genre, Movie, User
from load_data import load_open_data


PER_PAGE = 10


def create_app(test_config=None):
    database_url = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(os.getcwd(), "instance", "cineflix.sqlite"),
    )
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "cineflix-dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        if not app.config.get("TESTING"):
            load_open_data(db)

    register_template_helpers(app)
    register_routes(app)
    register_error_handlers(app)
    return app


def register_template_helpers(app):
    @app.context_processor
    def inject_helpers():
        return {"current_user": current_username}


def current_username():
    return session.get("username")


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            flash("Please log in to access that page.")
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)

    return wrapped_view


def safe_redirect_target(target):
    if not target:
        return None
    target_parts = urlsplit(target)
    if target_parts.netloc or target_parts.scheme:
        return None
    return target


def page_number():
    try:
        return max(1, int(request.args.get("page", 1)))
    except ValueError:
        abort(400)


def paginate_query(query, page, per_page=PER_PAGE):
    total = query.count()
    num_pages = max(1, math.ceil(total / per_page))
    page = min(page, num_pages)
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return {
        "items": items,
        "page": page,
        "num_pages": num_pages,
        "has_prev": page > 1,
        "has_next": page < num_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
        "total": total,
    }


def register_routes(app):
    @app.route("/")
    def index():
        return redirect(url_for("movie_list"))

    @app.route("/movies/")
    def movie_list():
        search = request.args.get("search", "").strip()
        genre_filter = request.args.get("genre", "").strip()

        query = Movie.query.join(Genre)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(Movie.title.ilike(search_pattern), Movie.director.ilike(search_pattern))
            )
        if genre_filter:
            query = query.filter(Movie.genre_code == genre_filter)

        query = query.order_by(Movie.title)
        pagination = paginate_query(query, page_number())
        return render_template(
            "movie_list.html",
            movies=pagination["items"],
            pagination=pagination,
            genres=Genre.query.order_by(Genre.name).all(),
            search_query=search,
            genre_filter=genre_filter,
        )

    @app.route("/movies/<movie_id>/")
    def movie_detail(movie_id):
        movie = db.session.get(Movie, movie_id)
        if not movie:
            abort(404)

        user = get_current_user()
        genre_count = Movie.query.filter_by(genre_code=movie.genre_code).count()
        genre_average = (
            db.session.query(func.avg(Movie.rating))
            .filter(Movie.genre_code == movie.genre_code)
            .scalar()
        )
        higher_rated_count = Movie.query.filter(Movie.rating > movie.rating).count()
        similar_movies = (
            Movie.query.filter(Movie.genre_code == movie.genre_code, Movie.source_code != movie.source_code)
            .order_by(Movie.rating.desc(), Movie.title)
            .limit(5)
            .all()
        )
        return render_template(
            "movie_detail.html",
            movie=movie,
            is_favourite=bool(user and user.favourite_movies.filter_by(source_code=movie_id).first()),
            genre_count=genre_count,
            genre_average=genre_average or 0,
            higher_rated_count=higher_rated_count,
            total_movies=Movie.query.count(),
            similar_movies=similar_movies,
        )

    @app.route("/movies/<movie_id>/favourite/", methods=["POST"])
    @login_required
    def toggle_favourite(movie_id):
        movie = db.session.get(Movie, movie_id)
        if not movie:
            abort(404)
        user = get_current_user()
        if user.favourite_movies.filter_by(source_code=movie_id).first():
            user.favourite_movies.remove(movie)
            flash("Removed from favourites.")
        else:
            user.favourite_movies.append(movie)
            flash("Added to favourites.")
        db.session.commit()
        return redirect(request.referrer or url_for("movie_detail", movie_id=movie_id))

    @app.route("/favourites/")
    @login_required
    def favourites_list():
        user = get_current_user()
        favourites = user.favourite_movies.all()
        return render_template("favourites_list.html", favourites=favourites)

    @app.route("/genres/<genre_code>/")
    def genre_detail(genre_code):
        genre = db.session.get(Genre, genre_code)
        if not genre:
            abort(404)
        query = Movie.query.filter_by(genre_code=genre_code).order_by(Movie.rating.desc(), Movie.title)
        pagination = paginate_query(query, page_number())
        stats = {
            "count": query.count(),
            "average_rating": db.session.query(func.avg(Movie.rating))
            .filter(Movie.genre_code == genre_code)
            .scalar()
            or 0,
            "average_runtime": db.session.query(func.avg(Movie.runtime_minutes))
            .filter(Movie.genre_code == genre_code)
            .scalar()
            or 0,
            "top_movie": query.first(),
        }
        return render_template(
            "genre_detail.html",
            genre=genre,
            movies=pagination["items"],
            pagination=pagination,
            stats=stats,
        )

    @app.route("/login/", methods=["GET", "POST"])
    def login():
        if get_current_user():
            return redirect(url_for("movie_list"))
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter(func.lower(User.username) == username.lower()).first()
            if user and user.check_password(password):
                session.clear()
                session["user_id"] = user.id
                session["username"] = user.username
                flash(f"Welcome back, {user.username}!")
                return redirect(safe_redirect_target(request.args.get("next")) or url_for("movie_list"))
            error = "Invalid username or password."
        return render_template("login.html", error=error)

    @app.route("/register/", methods=["GET", "POST"])
    def register():
        if get_current_user():
            return redirect(url_for("movie_list"))
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm", "")
            existing = User.query.filter(func.lower(User.username) == username.lower()).first()
            if not username or not password:
                error = "Username and password are required."
            elif existing:
                error = "That username is already taken."
            elif password != confirm:
                error = "Passwords do not match."
            elif len(password) < 8:
                error = "Password must be at least 8 characters long."
            else:
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                session.clear()
                session["user_id"] = user.id
                session["username"] = user.username
                flash(f"Account created. Welcome, {user.username}!")
                return redirect(url_for("movie_list"))
        return render_template("register.html", error=error)

    @app.route("/logout/", methods=["POST"])
    def logout():
        session.clear()
        flash("You have been logged out.")
        return redirect(url_for("movie_list"))


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("error.html", title="Bad request", message="That request could not be understood."), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("error.html", title="Server error", message="Something went wrong."), 500


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
