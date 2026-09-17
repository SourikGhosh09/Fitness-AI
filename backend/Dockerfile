FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/ .
COPY data/ /data/
ENV FITNESS_DATA_DIR=/data
RUN useradd --create-home fitness && chown -R fitness:fitness /app
USER fitness
EXPOSE 8000
CMD ["uvicorn","fitness.api:app","--host","0.0.0.0","--port","8000"]
