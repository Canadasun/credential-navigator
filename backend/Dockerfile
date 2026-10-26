# Backend API with local OCR (Tesseract): scanned documents are read inside this
# container and never sent to an outside service.
FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home api && chown -R api /app
USER api
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
