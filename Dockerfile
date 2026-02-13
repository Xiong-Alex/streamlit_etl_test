FROM python:3.11-slim

WORKDIR /app

# Copy root requirements file
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy contents of app/ folder into /app
# This flattens it so app.py ends up at /app/app.py
COPY app/ .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.runOnSave=true", "--server.fileWatcherType=poll"]
