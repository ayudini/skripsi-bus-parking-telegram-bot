FROM python:slim
WORKDIR /app
COPY .env app.py requirements.txt serviceAccountKey.json /app
RUN pip install -r requirements.txt
CMD python app.py