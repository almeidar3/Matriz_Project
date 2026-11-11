FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /app/instance \
    && chown app:app /app/instance

COPY --chown=app:app app.py auth.py db.py projects.py tasks.py ./
COPY --chown=app:app templates ./templates
COPY --chown=app:app static ./static

USER app
EXPOSE 10000

CMD ["sh", "-c", "if [ \"${MATRIX_SEED_DEMO:-0}\" = \"1\" ]; then flask --app app seed-demo; fi; exec gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 --access-logfile - --error-logfile - 'app:create_app()'"]