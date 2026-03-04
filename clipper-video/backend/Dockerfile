FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

COPY . /app/
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENV PORT=8080
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "clipper.wsgi:application", "--bind", ":8080", "--workers", "1", "--threads", "4", "--timeout", "300"]
