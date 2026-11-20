FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv
WORKDIR /app
COPY app.py .
# install the script's inline (PEP 723) dependencies at build time, then start plain python:
# a new pod is ready in about a second and never touches PyPI
RUN uv export --script app.py --no-hashes | uv pip install --system --no-cache --compile-bytecode -r -
CMD ["python", "app.py"]
