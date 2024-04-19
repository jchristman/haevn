FROM debian:latest

# Install curl and procps (for meteor)
RUN apt-get update && apt-get install -y curl procps
# Install meteor 1.1.0.2
RUN curl "https://install.meteor.com/?release=1.1.0.2" | sh

# Create working dir at /app
RUN mkdir /app
WORKDIR /app

# Copy the app to the container
COPY . /app

# Default run to bash -c "meteor npm install && meteor --allow-superuser"'
CMD ["bash", "-c", "meteor"]