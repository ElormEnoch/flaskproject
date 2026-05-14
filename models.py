from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def utc_now():
    return datetime.now(timezone.utc)


favourites = db.Table(
    "favourites",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("movie_id", db.String(20), db.ForeignKey("movies.source_code"), primary_key=True),
    db.Column("created_at", db.DateTime, default=utc_now, nullable=False),
)


class Genre(db.Model):
    __tablename__ = "genres"

    code = db.Column(db.String(12), primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False, default="")

    movies = db.relationship("Movie", back_populates="genre", lazy="dynamic")


class Movie(db.Model):
    __tablename__ = "movies"

    source_code = db.Column(db.String(20), primary_key=True)
    title = db.Column(db.String(180), nullable=False, index=True)
    genre_code = db.Column(db.String(12), db.ForeignKey("genres.code"), nullable=False, index=True)
    director = db.Column(db.String(120), index=True)
    year = db.Column(db.Integer, index=True)
    rating = db.Column(db.Float, index=True)
    runtime_minutes = db.Column(db.Integer)
    description = db.Column(db.Text)

    genre = db.relationship("Genre", back_populates="movies")

    @property
    def id(self):
        return self.source_code


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    favourite_movies = db.relationship(
        "Movie",
        secondary=favourites,
        lazy="dynamic",
        order_by="Movie.title",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
