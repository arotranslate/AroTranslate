FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y wget
RUN wget https://github.com/senisioi/AroTranslate/releases/download/test0/NLLB-rup-ron-eng-ct2-v2.tar.gz && \
    tar -xvf NLLB-rup-ron-eng-ct2-v2.tar.gz && \
    rm NLLB-rup-ron-eng-ct2-v2.tar.gz
COPY . .
EXPOSE 5000
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
#CMD ["flask", "run"]
