# One-shot loader: validates the regulator data and loads it into PostgreSQL.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home loader && chown -R loader /app
USER loader
CMD ["python", "update_matrices.py"]
