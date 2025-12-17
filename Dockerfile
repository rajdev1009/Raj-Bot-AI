FROM python:3.10-slim

WORKDIR /app

# System dependencies (Voice ke liye ffmpeg zaroori hai)
RUN apt-get update && apt-get install -y ffmpeg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
