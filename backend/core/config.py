import os
from contextlib import contextmanager

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://navigator:navigator-local-only@127.0.0.1:5433/navigator")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

DISCLAIMER = ("Advisory only. This comparison is for preparation and is not an academic assessment. "
              "APEGA's Board of Examiners alone decides which exams or courses an applicant must complete, "
              "based on the WES Course-by-Course report and its own review.")


@contextmanager
def connection():
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn
