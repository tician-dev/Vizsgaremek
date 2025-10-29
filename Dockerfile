
FROM python:3.12 as backend
ENV PYTHONUNBUFFERED=1
COPY ./api /api 
COPY ./api /api
COPY ./requirements.txt /api/requirements.txt
WORKDIR /api
RUN pip install -r /api/requirements.txt 
EXPOSE 8000