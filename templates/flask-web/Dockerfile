FROM python:3.12-slim
WORKDIR /srv/app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
COPY app ./app
COPY config.py ./
COPY migrations ./migrations
RUN pip install --no-cache-dir . gunicorn
# The platform router sets X-Forwarded-Prefix; the app honours it (app/wsgi_prefix.py).
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "app:create_app()"]
