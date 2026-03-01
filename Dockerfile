FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "UI/app.py", "--server.port=8501", "--server.address=0.0.0.0"]