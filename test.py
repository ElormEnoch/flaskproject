import pytest

from app import create_app
from extensions import db
from models import Genre, Movie, User
from load_data import load_open_data


@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
        }
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(Genre(code="ACT", name="Action", description="Action films"))
        db.session.add(Genre(code="DRA", name="Drama", description="Drama films"))
        db.session.add(
            Movie(
                source_code="M0001",
                title="Star Force",
                genre_code="ACT",
                director="Joe Carnahan",
                year=1967,
                rating=6.3,
                runtime_minutes=78,
                description="A teacher goes off the grid.",
            )
        )
        db.session.add(
            Movie(
                source_code="M0002",
                title="A Bitter Life",
                genre_code="DRA",
                director="Hirokazu Kore-eda",
                year=1983,
                rating=7.2,
                runtime_minutes=89,
                description="A soldier fights for justice.",
            )
        )
        db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="alice", password="password123"):
    return client.post(
        "/register/",
        data={"username": username, "password": password, "confirm": password},
        follow_redirects=True,
    )


def test_movie_list_uses_database_records(client):
    response = client.get("/movies/?search=Star")

    assert response.status_code == 200
    assert b"Star Force" in response.data
    assert b"A Bitter Life" not in response.data


def test_movie_detail_shows_dataset_context(client):
    response = client.get("/movies/M0001/")

    assert response.status_code == 200
    assert b"Dataset context" in response.data
    assert b"Action movies in this dataset" in response.data


def test_invalid_page_returns_400(client):
    response = client.get("/movies/?page=banana")

    assert response.status_code == 400
    assert b"Bad request" in response.data


def test_registration_login_and_favourite_flow(client):
    response = register(client)

    assert response.status_code == 200
    assert b"Account created" in response.data

    response = client.post("/movies/M0001/favourite/", follow_redirects=True)
    assert response.status_code == 200
    assert b"Added to favourites." in response.data

    response = client.get("/favourites/")
    assert b"Star Force" in response.data


def test_protected_favourites_redirects_to_login(client):
    response = client.get("/favourites/")

    assert response.status_code == 302
    assert "/login/" in response.headers["Location"]


def test_passwords_are_hashed(app):
    with app.app_context():
        user = User(username="bob")
        user.set_password("password123")

        assert user.password_hash != "password123"
        assert user.check_password("password123")


def test_data_loader_loads_expected_open_data_volume(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        load_open_data(db)

        assert Movie.query.count() == 4000
        assert Genre.query.count() >= 2
