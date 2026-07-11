FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ ./api/
COPY sql/ ./sql/
COPY deploy_views.py ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port
EXPOSE 8080

# Command to run the backend
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
