FROM python:3.11-slim
WORKDIR /app
COPY /app .
COPY . .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "5", "--threads", "2", "flashcards:app"]