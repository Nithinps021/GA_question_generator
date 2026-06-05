FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY telegram/ telegram/
COPY prompt/ prompt/
COPY start.sh start.sh

# 5. Make your start script executable
RUN chmod +x start.sh

# 6. Execute the script using the exec array form
CMD ["./start.sh"]
