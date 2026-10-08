FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tini ca-certificates && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash --uid 10001 app
WORKDIR /app
# BUILD CONTEXT IS deploy/, as for the chat service: the bridge imports shared/iap.py, desk_rules.py and desk_law.py.
#     docker build -f services/gchat/Dockerfile -t documind-gchat .      # run from deploy/
COPY services/gchat/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app shared/ ./shared/
COPY --chown=app:app services/gchat/ ./
USER app
ENV PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
HEALTHCHECK --interval=20s --timeout=3s --start-period=15s CMD python -c "import urllib.request as r; r.urlopen('http://localhost:8080/health').read()" || exit 1
ENTRYPOINT ["/usr/bin/tini", "--"]
# -t 300: a push takes at most 260 s, 180 for the Desk and four posts of 20 (main.py WORK_TIMEOUT_S), under 300.
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "1", "-b", "0.0.0.0:8080", "-t", "300", "--access-logfile", "-", "main:app"]
