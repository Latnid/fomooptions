# Use the selenium/standalone-firefox image as the base image
FROM seleniarm/standalone-chromium:latest

# Set the working directory to /app
WORKDIR /app

# Copy the files from the current directory into the container's /app directory
COPY . .

# Expose ports 4444, 5900, and 7900
EXPOSE 4444 5900 7900

# Install sudo for root access during package installation
USER root

# Install Python and other dependencies using sudo
RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip3 install -r requirements.txt --break-system-packages

# Set the owner and group of /home/seluser to seluser

RUN mkdir -p /home/seluser/Downloads
RUN chown -R seluser:root /home/seluser
RUN chown -R seluser:root /app/
COPY ./Sysetting/selenium.conf /etc/supervisor/conf.d 

# Start the Python script when the container runs
USER seluser

