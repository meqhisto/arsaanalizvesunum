FROM python:3.10-slim

# Kurulum için gerekli bağımlılıkları ekleyelim (özellikle pyodbc için)
RUN apt-get update && apt-get install -y \
    gcc \
    unixodbc-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Node.js kurulumu (Frontend derlemesi için)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python gereksinimlerini kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Node gereksinimlerini kopyala ve yükle
COPY package.json package-lock.json* ./
RUN npm install

# Uygulama kodlarını kopyala
COPY . .

# Frontend bağımlılıklarını derle
RUN npm run build

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
