uv pip compile pyproject.toml -o requirements.txt

# Generate dev requirements (includes both production and dev dependencies)
uv pip compile pyproject.toml --extra dev -o requirements-dev.txt