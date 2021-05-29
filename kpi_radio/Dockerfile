# syntax=docker/dockerfile:experimental
FROM python:3.9-slim
WORKDIR /kpi_radio
COPY requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY . .
EXPOSE 443
CMD ["python", "."]
