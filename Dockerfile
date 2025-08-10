# Multi-stage build for computer-use-mcp
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY requirements-health.txt .
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r requirements-health.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies for X11 and screenshot tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    scrot \
    imagemagick \
    x11-utils \
    xvfb \
    xauth \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxrandr2 \
    libxcursor1 \
    libxinerama1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set PATH to include user site packages
ENV PATH=/root/.local/bin:$PATH

# Create app directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY bin/ ./bin/
COPY examples/ ./examples/
COPY package.json ./
COPY README.md ./

# Make bin scripts executable
RUN chmod +x ./bin/computer-use-mcp

# Create volume for shared state and logs
VOLUME ["/app/data", "/tmp/.X11-unix"]

# Environment variables for X11
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Expose port for MCP communication (if needed)
EXPOSE 3333

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.path.append('/app/src'); from mcp_server import ComputerUseServer; print('OK')" || exit 1

# Default command - run with virtual display
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & python3 /app/src/mcp_server.py"]

# Alternative entry point for development
# ENTRYPOINT ["/app/bin/computer-use-mcp"]