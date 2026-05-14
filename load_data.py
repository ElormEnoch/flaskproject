import csv
import os

from models import Genre, Movie


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _clean_int(value):
    value = (value or "").strip()
    return int(value) if value else None


def _clean_float(value):
    value = (value or "").strip()
    return float(value) if value else None


def load_open_data(db):
    """Load the open movie dataset into SQLite once."""
    if Movie.query.first():
        return

    genres = {}
    with open(os.path.join(DATA_DIR, "genres.csv"), encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            code = row.get("code", "").strip()
            if not code:
                continue
            genre = Genre(
                code=code,
                name=row.get("name", "").strip(),
                description=row.get("description", "").strip(),
            )
            genres[code] = genre
            db.session.add(genre)

    with open(os.path.join(DATA_DIR, "movies.csv"), encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            genre_code = row.get("genre_code", "").strip()
            if genre_code not in genres:
                genre = Genre(code=genre_code, name=genre_code, description="")
                genres[genre_code] = genre
                db.session.add(genre)

            db.session.add(
                Movie(
                    source_code=row.get("source_code", "").strip(),
                    title=row.get("title", "").strip(),
                    genre_code=genre_code,
                    director=(row.get("director", "").strip() or None),
                    year=_clean_int(row.get("year")),
                    rating=_clean_float(row.get("rating")),
                    runtime_minutes=_clean_int(row.get("runtime_minutes")),
                    description=(row.get("description", "").strip() or None),
                )
            )

    db.session.commit()
