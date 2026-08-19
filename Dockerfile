FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies and Microsoft ODBC Driver 18
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
        unixodbc \
        unixodbc-dev \
        gcc \
        g++ \
    && curl -sSL -O \
        https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY config.py .
COPY storage.py .
COPY rest_api.py .
COPY mcp_server.py .

RUN mkdir -p /app/data

EXPOSE 8000 8001

CMD ["uvicorn", "rest_api:app", "--host", "0.0.0.0", "--port", "8000"]