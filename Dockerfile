FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
# Using requirements.txt for cleaner image management
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from current directory to /app
COPY . .

# Ensure the /data directory exists (for volume mapping)
RUN mkdir -p /data

# Expose the default FastMCP port for SSE (standard: 8000)
EXPOSE 8000

# Run the MCP server
# Note: Host must be set to 0.0.0.0 for container access
# The fastmcp library's .run() usually respects MCP_HOST or similar,
# but can be explicitly set in the app.py if needed.
CMD ["python", "app.py"]
