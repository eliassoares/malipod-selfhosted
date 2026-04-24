FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv==0.8.15

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["sh", "-c", ".venv/bin/alembic upgrade head && .venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w $(( $(nproc) > 8 ? 8 : $(nproc) )) --bind 0.0.0.0:8000"]
