FROM python:3.9-slim
WORKDIR /app
COPY careermark/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY careermark/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
