#!/bin/bash

# Navigate to your project directory (adjust path as necessary)
cd /home/hamishburke/Tapo-Light-API

# Activate the virtual environment
source venv/bin/activate

# Run the Quart app
authbind --deep python3 main.py

