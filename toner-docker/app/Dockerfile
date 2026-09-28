# syntax=docker/dockerfile:1.7
# ---------- dependencies ----------
FROM python:3.12-slim AS deps
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt /tmp/requirements.txt
RUN pip install --prefix=/install -r /tmp/requirements.txt

# ---------- runtime ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MALLOC_ARENA_MAX=2

RUN groupadd --system --gid 10001 toner \
 && useradd --system --uid 10001 --gid toner --no-create-home --home-dir /app --shell /usr/sbin/nologin toner \
 && rm -rf /var/lib/apt/lists/* /root/.cache

COPY --from=deps /install /usr/local
WORKDIR /app
COPY --chown=root:root toner ./toner
COPY --chown=root:root static ./static
# Onest (SIL Open Font License), served locally: the page loads nothing from the internet
ADD --chmod=644 https://cdn.jsdelivr.net/npm/@fontsource-variable/onest@5.3.1/files/onest-cyrillic-wght-normal.woff2 ./static/fonts/
ADD --chmod=644 https://cdn.jsdelivr.net/npm/@fontsource-variable/onest@5.3.1/files/onest-latin-wght-normal.woff2 ./static/fonts/
RUN chmod -R a+rX /app && mkdir -p /app/branding

USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=4).status == 200 else 1)"]
STOPSIGNAL SIGTERM
CMD ["python", "-m", "toner"]
