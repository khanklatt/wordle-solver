# Dockerfile for Wordle Solver Web Application
# Requirement 7.1: Containerized using Docker

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY wordle_solver.py /app/
COPY lib/ /app/lib/
COPY api/ /app/api/
COPY web/ /app/web/

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=api/app.py
ENV FLASK_ENV=production

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "api.app:app"]

