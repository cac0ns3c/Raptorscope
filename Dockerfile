# SPDX-License-Identifier: GPL-3.0-or-later
# Raptorscope API image. Default command serves the bundled sample case offline
# (no ES needed); the compose "app" profile overrides it to serve from ES.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -e .

COPY detections ./detections
COPY samples ./samples
COPY profile ./profile
COPY docs ./docs
COPY README.md ./

EXPOSE 8000
CMD ["raptorscope", "serve", "--collection", "samples/mac-victim", \
     "--host", "0.0.0.0", "--port", "8000"]
