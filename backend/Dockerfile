FROM python:3.11-slim

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code and migrations
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Create storage mount directory
RUN mkdir -p /app/storage

ENV PYTHONPATH=/app
ENV PORTAL_MODE=DEVELOPMENT
ENV STORAGE_PROVIDER=local
ENV LOCAL_STORAGE_PATH=/app/storage

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

