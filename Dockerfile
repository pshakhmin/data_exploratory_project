FROM python:3.11.6-slim

COPY ./app /flask_app
COPY requirements.txt /

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir waitress 

WORKDIR /flask_app

CMD [ "waitress-serve", "app:app" ]
