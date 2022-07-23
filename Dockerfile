FROM python:3.10-slim
RUN pip install poetry
COPY poetry.lock pyproject.toml .
RUN poetry install
COPY app app
COPY .env .env
EXPOSE 8000
CMD poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080