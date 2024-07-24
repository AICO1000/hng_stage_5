#!/bin/bash

# Function to wait for other apt processes to finish
wait_for_apt() {
    while sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 ; do
       echo "Waiting for other apt processes to finish..."
       sleep 1
    done
}

# Wait for other apt processes to finish
wait_for_apt

# Update package lists
sudo apt update

# Install necessary packages
sudo apt install -y python3 python3-pip python3-venv nginx docker.io logrotate

# Create a virtual environment and activate it
python3 -m venv devopsfetch-env
source devopsfetch-env/bin/activate

# Install Python dependencies
pip install psutil docker argparse

# Create a systemd service file
sudo tee /etc/systemd/system/devopsfetch.service > /dev/null <<EOL
[Unit]
Description=Devopsfetch Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/devopsfetch-env/bin/python $(pwd)/devopsfetch.py -l
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable and start the devopsfetch service
sudo systemctl enable devopsfetch.service
sudo systemctl start devopsfetch.service

# Create logrotate configuration
sudo tee /etc/logrotate.d/devopsfetch > /dev/null <<EOL
/var/log/devopsfetch.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0640 $(whoami) adm
    postrotate
        sudo systemctl reload devopsfetch > /dev/null 2>/dev/null || true
    endscript
}
EOL

echo "Installation and setup completed. The devopsfetch service is now running."
