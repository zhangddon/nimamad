FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN mkdir -p /app/logs /app/outputs

EXPOSE 8787
CMD ["python3", "control_panel.py", "--host", "0.0.0.0", "--port", "8787"]
