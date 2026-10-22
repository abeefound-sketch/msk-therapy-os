# Hugging Face Docker Space: synthetic read-only demonstration, no pip/npm.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MSK_PUBLIC_DEMO_READONLY=1 \
    PORT=7860
WORKDIR /app
COPY msk_therapy_os/ ./msk_therapy_os/
COPY deploy/ ./deploy/
RUN useradd --uid 1000 --create-home appuser && mkdir -p /app/data && chown -R appuser:appuser /app/data
USER appuser
EXPOSE 7860
CMD ["sh", "deploy/start-space.sh"]
