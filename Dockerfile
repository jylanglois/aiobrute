FROM python:3.10-bullseye

COPY . /app/aiobrute
WORKDIR  /app/aiobrute

RUN python -m venv /app/venv
RUN /app/venv/bin/pip install -r requirements.txt

ENTRYPOINT [ "/app/venv/bin/python", "aiobrute.py" ]