FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app
RUN groupadd --system app && \
    useradd --system --gid app --uid 10001 --create-home app && \
    mkdir -p /app/data && \
    chown -R app:app /app

USER app

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3); sys.exit(0)"

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
