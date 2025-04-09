# Use Node.js as base image
FROM node:18

# Install Python, pip, and system dependencies for whisper
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Node.js dependencies
COPY package*.json ./
RUN npm install

# Install Python dependencies with verbose output
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --verbose > pip_install.log 2>&1 || (cat pip_install.log && exit 1)

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Start the app
CMD ["node", "index.js"]