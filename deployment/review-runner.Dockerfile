FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
USER 65534:65534
CMD ["python", "-B", "-m", "unittest", "discover", "-v"]
