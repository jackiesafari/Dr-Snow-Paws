#!/bin/bash

# Get the PORT environment variable or default to 8080
PORT=${PORT:-8080}

# Start the application with the correct port
uvicorn main:app --host 0.0.0.0 --port $PORT 