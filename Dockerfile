FROM python:3.11

WORKDIR /code

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY ./app /code/app
COPY .env /code/

EXPOSE 50505

ENTRYPOINT ["gunicorn", "-w 4", "-k uvicorn.workers.UvicornWorker", "-b 0.0.0.0:8000", "app.backend:app"]
