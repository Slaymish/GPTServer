FROM python:3.9 

WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy your application code
COPY . . 

# Expose the port 
EXPOSE 8080

# Command to start the app 
CMD ["python", "main.py"]