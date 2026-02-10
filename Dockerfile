
FROM python:3.13-slim
WORKDIR /app
COPY app /app/app
COPY templates /app/templates
COPY static /app/static
RUN pip install fastapi uvicorn pyworxcloud jinja2
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
