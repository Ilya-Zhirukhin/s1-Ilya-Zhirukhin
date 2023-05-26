FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
COPY ../data/site.sqlite3 /app/data/site.sqlite3


CMD ["python", "run.py"]
