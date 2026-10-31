FROM node:22-bookworm-slim AS cli
WORKDIR /cli
COPY package.json package-lock.json ./
RUN npm ci --omit=optional

FROM python:3.13-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ADK_DATA_DIR=/app/data ADK_ARTIFACT_DIR=/app/artifacts/local
COPY --from=cli /usr/local/bin/node /usr/local/bin/node
COPY --from=cli /cli/node_modules ./node_modules
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY assignment ./assignment
COPY agents ./agents
COPY config ./config
COPY examples ./examples
RUN pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home appuser && mkdir -p data artifacts/local && chown -R appuser:appuser data artifacts /home/appuser
USER appuser
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "assignment.api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
