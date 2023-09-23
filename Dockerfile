FROM python:alpine
WORKDIR /app
COPY . /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
CMD python app.py