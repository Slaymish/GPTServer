# Use the official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV PORT 8080
ENV TAPO_USERNAME hamishapps@gmail.com
ENV TAPO_PASSWORD l1tHyr~s

# Run app.py when the container launches
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:$PORT"]