# Who's Next?

A Python-based web application to manage and track software release responsibilities using a round-robin algorithm. Built with FastAPI, SQLite, and raw Javascript.

## Features
- **Round-Robin Release Determination:** Automatically determines who is next to perform a release based on the lowest release count.
- **Participant Management:** Keep a record of participants (first name & last name).
- **Release History:** Log every software release with its date, version, and the participant who executed it.
- **Modern User Interface:** A fast, responsive Single Page Application with dynamic animations and dark-mode glassmorphism styling.

## Prerequisites
- [uv](https://github.com/astral-sh/uv) installed
- Python 3.14 or later

## Setup
You don't need to manually create virtual environments. `uv` handles dependency management automatically.

1. Clone or navigate to the repository:
   ```bash
   cd whosnext
   ```

2. (Optional) Create a `.env` file in the project root to override the SQLite database location:
   ```env
   DB_PATH=/custom/path/whosnext.db
   ```
   If omitted, `whosnext.db` will be created automatically in the root folder.

## Starting the Program

To run the FastAPI server, use `uv run uvicorn` from the root of the project:

```bash
uv run uvicorn src.main:app --reload
```

Once started, open your browser and navigate to:
[http://127.0.0.1:8000](http://127.0.0.1:8000)

## Running the Tests

Unit tests are written using `pytest` and utilize an in-memory SQLite database. To execute the test suite, run:

```bash
uv run pytest
```
