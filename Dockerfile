# Dockerfile for Chifleton (dependency vulnerability scanner).
# Build: docker build -t chifleton .
# Run scan: docker run --rm -v "$(pwd):/work" -w /work chifleton scan /work/requirements.txt --report html

FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY scanner ./scanner/

RUN pip install --no-cache-dir .

# Default: run scan on requirements.txt in current dir when used as:
#   docker run --rm -v $(pwd):/work -w /work chifleton
ENTRYPOINT ["chifleton"]
CMD ["scan", "requirements.txt", "--report", "html"]
