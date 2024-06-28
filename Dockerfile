# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install required system packages
RUN apt update && apt install -y --no-install-recommends \
    curl \
    vim \
    poppler-utils \
    tesseract-ocr \
    nodejs \
    npm \
    libtesseract-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pdfplumber \
    pdf2image \
    pyocr \
    ipdb \
    python-dotenv \
    openai \
    anthropic \
    flask \
    jsonschema

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Define environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Create a new user "pothos"
RUN useradd -m pothos

# Install Node.js dependencies
WORKDIR /home/pothos/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

# Set the working directory in the container
COPY entrypoint.sh /home/pothos/
WORKDIR /home/pothos
RUN chown pothos:pothos /home/pothos/entrypoint.sh

# Change to non-root privilege
USER pothos
RUN chmod +x /home/pothos/entrypoint.sh

# Define environment variable for pretty terminal colors
ENV TERM=xterm-256color

# Run bash when the container launches
ENTRYPOINT ["/home/pothos/entrypoint.sh"]
CMD ["/bin/bash"]

