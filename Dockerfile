FROM python:3.11-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup -S app && adduser -S -G app -h /app app
WORKDIR /app

COPY pyproject.toml README.md ./
COPY requirements ./requirements
COPY src ./src
RUN pip install --upgrade pip \
    && pip install -c requirements/constraints.txt .

COPY alembic.ini ./
COPY migrations ./migrations

USER app
EXPOSE 8000
CMD ["uvicorn", "education_erp.main:app", "--host", "0.0.0.0", "--port", "8000"]
