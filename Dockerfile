FROM python:3.10-slim AS base

WORKDIR /opt/app
COPY . /opt/app
RUN python -m venv .venv && .venv/bin/pip install -r requirements.txt

ENV PATH="/opt/app/.venv/bin:${PATH}"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
