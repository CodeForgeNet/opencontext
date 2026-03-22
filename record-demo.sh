#!/bin/bash
# PCSL Demo Recording Script
# Run this script to record the terminal session for the GIF

# Set PATH to include pcsl
export PATH="/Users/karansingh/Desktop/PCSL_main/venv/bin:$PATH"

# Terminal setup for recording
export COLUMNS=100

echo "Starting PCSL Demo Recording..."
echo "Press Ctrl+C to stop recording"
echo ""

# Record with asciinema
asciinema rec pcsl-demo.cast --title "PCSL Demo"

# Convert to GIF (after stopping recording)
# agg pcsl-demo.cast pcsl-demo.gif
