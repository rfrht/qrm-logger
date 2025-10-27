# Running qrm-logger as a Service on Raspberry Pi

For headless 24/7 monitoring, qrm-logger includes pre-configured systemd service files for easy installation on Raspberry Pi.


## Prerequisites

- Raspberry Pi running Raspberry Pi OS (or compatible Linux distribution)
- qrm-logger installed and working in console mode
- SDR device connected and recognized

## Installation Steps

### 1. Customize Service Files

**Edit the startup script** (`qrm-logger.sh` inside `service` directory):

Adjust the conda/mamba path to match your installation:
```
#!/bin/bash
source /home/pi/miniforge3/bin/activate qrm-logger  # Adjust path if needed
python main.py > application.log 2>&1
```

**Move/copy the startup script** from `service` directory to project root directory.


**Edit the service file** (`service/qrm-logger.service`):
```
nano service/qrm-logger.service
```

Adjust username and path if needed:
```ini
[Unit]
Description=qrm-logger
After=network.target

[Service]
ExecStart=/home/pi/qrm-logger/qrm-logger.sh  # Adjust path
Restart=always
User=pi                                      # Adjust username if needed
WorkingDirectory=/home/pi/qrm-logger         # Adjust path

[Install]
WantedBy=multi-user.target
```

### 2. Install Service

```
# Make startup script executable
chmod +x qrm-logger.sh

# Run the installation script
cd service
chmod +x service_install.sh
sudo ./service_install.sh
```

The installation script will:
- Copy the service file to `/etc/systemd/system/`
- Enable the service to start on boot
- Start the service immediately

### 3. Verify Installation

Check that the service is running:
```
sudo systemctl status qrm-logger
```

You should see output indicating the service is active and running.

## Service Management Commands

```
# Check service status
sudo systemctl status qrm-logger

# View application logs (follow mode)
tail -f -n 300 application.log

# View system logs (follow mode)
sudo journalctl -u qrm-logger -n 100 -f

# Stop/start/restart service
sudo systemctl stop qrm-logger
sudo systemctl start qrm-logger
sudo systemctl restart qrm-logger

# Enable/disable service from starting on boot
sudo systemctl enable qrm-logger
sudo systemctl disable qrm-logger
```

## Configuration for Headless Operation

For fully automated headless operation, edit the appropriate config files (see `config/` directory)

```python
# Edit config/web_server.py for network access:
web_server_host = '0.0.0.0'

# Edit config/scheduler_settings.py for auto-start:
scheduler_autostart = True
```

**Important Configuration Notes:**
- **Network Access**: Setting `web_server_host = '0.0.0.0'` allows access from other devices on your network
- **Security**: Only use `0.0.0.0` on trusted networks since there is no authentication


## Troubleshooting

### Service Won't Start
```
# Check for errors in the logs
sudo journalctl -u qrm-logger -n 20

# Common issues:
# - Incorrect paths in qrm-logger.sh or service file
# - Conda environment not found
# - Permission issues
# - SDR device not accessible
```

### SDR Device Permissions
Ensure the service user has access to USB devices:
```
# Check if user is in plugdev group
groups pi

# Add user to plugdev group if needed
sudo usermod -a -G plugdev pi
```

### Application Logs
The application logs are written to `application.log` in the working directory:
```
# View application logs
tail -n 300 -f /home/pi/qrm-logger/application.log
```

## File Permissions

Ensure the service user has proper permissions:
```

# Ensure startup script is executable
chmod +x /home/pi/qrm-logger/qrm-logger.sh
```

## Monitoring and Maintenance

### Regular Maintenance Tasks
- Monitor disk space (spectrum plots can accumulate over time)
- Check logs periodically for errors
- **IMPORTANT:** Monitor SDR device temperature in continuous operation

### Log Rotation
Consider setting up log rotation for `application.log`:
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/qrm-logger
```

Add the following content:
```
/home/pi/qrm-logger/application.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
```

## Uninstalling the Service

To remove the service:
```bash
# Stop and disable service
sudo systemctl stop qrm-logger
sudo systemctl disable qrm-logger

# Remove service file
sudo rm /etc/systemd/system/qrm-logger.service

# Reload systemd configuration
sudo systemctl daemon-reload
```

## Performance Considerations

For optimal performance on Raspberry Pi:
- Consider reducing FFT size via the web interface or by editing the JSON config file if CPU usage is high
- Monitor CPU temperature during continuous operation
- Use a fast SD card (Class 10 or better) or USB drive for storage
- Ensure adequate power supply (especially important for Pi 4 with SDR devices)
