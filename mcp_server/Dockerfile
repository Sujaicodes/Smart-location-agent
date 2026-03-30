FROM python:3.11-slim

WORKDIR /app

COPY mcp_server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY data/ ./data/
COPY mcp_server/server.py ./server.py

ENV USE_SQLITE=true
ENV USE_MOCK=false
ENV PORT=8080

EXPOSE 8080

CMD ["python", "server.py"]
