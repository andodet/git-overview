FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get -y install git

COPY . .

RUN pip install -r requirements.txt

WORKDIR app/

EXPOSE 8080
ENTRYPOINT ["streamlit","run"]
CMD ["dashboard.py", "--server.port=8080", "--server.address=0.0.0.0"]
