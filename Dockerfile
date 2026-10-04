# Python o'rnatilgan yengil operatsion tizimni olamiz
FROM python:3.11-slim

# yt-dlp video va musiqa yuklab olishi uchun zarur bo'lgan ffmpeg dasturini o'rnatamiz
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Ishchi papkani belgilaymiz
WORKDIR /app

# Kutubxonalar ro'yxatini ko'chiramiz va o'rnatamiz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha fayllarni (main.py va boshqalar) serverga ko'chiramiz
COPY . .

# Botni ishga tushiruvchi buyruq
CMD ["python", "main.py"]