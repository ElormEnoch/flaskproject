# Flask Movie Browser

## 1. Project Summary
This is a Flask web application for browsing and exploring movies and genres. It uses server-side rendering with Jinja2 templates and stores movie data in a local SQLite database.

## 2. Project Scope and Purpose
The app provides a clean interface to list movies, view movie details, explore genres, and manage favorites. It is designed using Flask, SQLAlchemy, and basic web application patterns.

## 3. Document and README Responsibilities
This README explains how to install, run, and maintain the project. It also documents the app structure, dependencies, and deployment guidelines.

## 4. Why the App Was Developed
- To create a practical Flask project with database-backed pages.
- To demonstrate template rendering, routing, and application design.
- To support browsing an open movie dataset in a simple UI.
- To practice integrating Flask with SQLAlchemy and local data import.
- To enable an easy-to-run example for development and testing.

## 5. How the App Was Developed
- Built with Flask for the web framework.
- Used `Flask-SQLAlchemy` for the ORM and database access.
- Loaded movie and genre data from CSV files in `data/`.
- Structured templates under `templates/` for list and detail pages.
- Implemented an application factory in `app.py` to create the Flask app cleanly.

## 6. Installation Instructions
1. Clone the repository(git clone https://github.com/ElormEnoch/flaskproject.git)
2. Create and activate a Python virtual environment - `python -m venv .venv` and `.\.venv\Scripts\activate` for Windows 
`python3 -m venv .venv` and `source .venv/bin/activate` for MacOS
3. Install dependencies with:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure the data files `data/genres.csv` and `data/movies.csv` are present.

## 7. Running the App and Render URL
Start the server with the Flask factory command:
```bash
flask --app app:create_app run --debug
```
Then open:

`http://127.0.0.1:5000`

Render url: https://flaskproject-wvqf.onrender.com/movies/


## 8. Maintenance Details
- Update `requirements.txt` when dependencies change.
- Keep `templates/` filenames synced with `render_template()` calls.
- Use the `instance/` folder to store the SQLite database safely.
- If the app fails to import, verify the virtual environment and installed packages.
- Keep CSV data consistent and reload via `load_data.py` if content changes.
- Manage database schema updates through SQLAlchemy models in `models.py`.
- Review `app.py` for new routes or helper function changes.

## 9. Additional Notes
- The application factory pattern makes the app easier to test and extend.
- A separate `extensions.py` file centralizes the DB initialization.
- Templates include `movie_list.html`, `movie_detail.html`, `genre_detail.html`, and `favourites_list.html`.
- The default database file is `instance/cineflix.sqlite`.

## 10. Future Improvements
- Add user authentication and login support.
