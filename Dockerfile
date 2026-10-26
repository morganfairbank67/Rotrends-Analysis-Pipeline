FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-dashboard.txt .
RUN pip install -r requirements-dashboard.txt

COPY .streamlit .streamlit
COPY Analytics Analytics
COPY Cloud_Database Cloud_Database
COPY Dashboard Dashboard
COPY streamlit_app.py .

RUN useradd --create-home app && chown -R app /app
USER app

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
