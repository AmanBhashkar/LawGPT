#!/bin/bash

# Clean Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete

# Remove environment files if they exist
rm -f .env .env.*

# Clean Docker artifacts
docker-compose down --volumes --rmi local

echo "Cleanup complete! Remember to recreate your .env file if needed." 