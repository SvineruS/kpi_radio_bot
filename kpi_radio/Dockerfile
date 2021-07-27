FROM python:3.9-slim
WORKDIR /kpi_radio
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
EXPOSE 443
CMD ["python", "."]