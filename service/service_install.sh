#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi
set -x

echo "Make sure to adjust username & path in qrm-logger.service"
echo "And move qrm-logger.sh to project root directory & make it executable"


cp qrm-logger.service /etc/systemd/system/qrm-logger.service

systemctl enable qrm-logger.service
systemctl start qrm-logger.service

