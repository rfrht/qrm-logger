#!/bin/bash

# move this file to project root, adjust the path to conda bin & make it executable
source /home/pi/miniforge3/bin/activate qrm-logger

python main.py > application.log 2>&1