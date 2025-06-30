FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    imagemagick \
    imagemagick-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy for text overlay
RUN echo '<?xml version="1.0" encoding="UTF-8"?>' > /etc/ImageMagick-6/policy.xml && \
    echo '<!DOCTYPE policymap [' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ELEMENT policymap (policy)+>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ELEMENT policy EMPTY>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ATTLIST policy domain (delegate|coder|filter|path|resource) #IMPLIED>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ATTLIST policy name CDATA #IMPLIED>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ATTLIST policy pattern CDATA #IMPLIED>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ATTLIST policy rights CDATA #IMPLIED>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ATTLIST policy stealth (True|False) "False">' >> /etc/ImageMagick-6/policy.xml && \
    echo '<!ATTLIST policy value CDATA #IMPLIED>' >> /etc/ImageMagick-6/policy.xml && \
    echo ']>' >> /etc/ImageMagick-6/policy.xml && \
    echo '<policymap>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="resource" name="memory" value="256MiB"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="resource" name="map" value="512MiB"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="resource" name="width" value="16KP"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="resource" name="height" value="16KP"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="resource" name="area" value="128MB"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="resource" name="disk" value="1GiB"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="path" rights="read|write" pattern="@*"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="TEXT"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '  <policy domain="coder" rights="read|write" pattern="LABEL"/>' >> /etc/ImageMagick-6/policy.xml && \
    echo '</policymap>' >> /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Copy requirements and install dependencies
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads output youtube_downloads

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]