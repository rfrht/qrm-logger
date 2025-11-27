

## Configuration

qrm-logger uses a hybrid configuration system that combines file-based defaults with web-configurable runtime settings:

### Configuration Architecture

**Static Configuration (config/ directory)**
- Contains all default configuration values organized in separate modules:
  - `capture_definitions.py` - Frequency ranges and capture sets
  - `band_definitions.py` - Amateur radio band markers
  - `sdr_hardware.py` - SDR device types and settings
  - `output_directories.py` - File output locations
  - `web_server.py` - Web interface network settings
  - `scheduler_settings.py` - Automated recording settings
- Modified by editing the files directly - requires application restart

**Dynamic Configuration (JSON)**
- Automatically managed by the configuration system in `config.json`
- Contains runtime-adjustable parameters duplicated from Python config files:
  - `rf_gain` (from `sdr_hardware.py`)
  - `sdr_bandwidth` (calculated from device defaults)
  - `rec_time_default_sec` (from `recording_params.py`)
  - `scheduler_cron`, `scheduler_autostart` (from `scheduler_settings.py`)
  - `fft_size`, `min_db`, `max_db` (from `recording_params.py`)
  - `capture_sets_enabled` (derived from `capture_definitions.py`)
- Can be modified through the web interface without restarting the application
- Persists settings between sessions
- **IMPORTANT**: If you modify default values in the Python config files, delete `config.json` to force regeneration with new defaults

### Getting Started

1. **Initial Setup**: Edit the appropriate files in the `config/` directory to set your preferred frequency ranges, SDR device type, and other structural settings
2. **Runtime Adjustments**: Use the web interface to fine-tune gain, recording time, and other operational parameters

### Important: Python Config Changes Workflow

When you modify default values in the Python configuration files, follow this workflow:

1. **Edit Python Config Files**: Make your changes to files like `sdr_hardware.py`, `recording_params.py`, etc.
2. **Delete JSON Config**: Remove the `config.json` file
3. **Restart Application**: The application will recreate `config.json` with your new default values
4. **Verify Settings**: Check the web interface to confirm your new defaults are active

**Why This is Necessary**: The JSON config file takes precedence over Python defaults once it exists. If you don't delete it, your Python changes will be ignored because the application will continue using the cached values from the JSON file.

### Adding New Capture Sets

Capture sets define the frequency ranges that qrm-logger will monitor. They are configured in `config/capture_definitions.py`.

#### Built-in Capture Sets

**hf_bands**
- Monitors specific amateur radio HF bands: 80m, 40m, 30m, 20m, 17m, 15m, and 10m
- Uses band-specific center frequencies optimized for amateur radio activity
- Ideal for focused monitoring of ham radio frequencies

**hf_full** 
- Comprehensive HF coverage from 0-30 MHz in 2 MHz steps
- **Best used with 2.4 MHz bandwidth setting**
- Uses frequency cropping to avoid FFT problems at frequency corners
- Provides complete HF spectrum coverage with good resolution
- Works with most SDR devices

**hf_full_wide**
- Wideband HF coverage from 3-30 MHz in 5 MHz steps
- **Best used with 6 MHz bandwidth setting**
- Uses frequency cropping to avoid FFT problems at frequency corners
- Optimized for high bandwidth SDRs that support wider spans
- More efficient capture for wideband-capable SDRs



#### Creating or Editing Capture Sets (JSON)

All capture sets are defined in a single JSON file at the project root: `capture_sets.json`.

- The file is created automatically on first run with sensible defaults.
- It is git-ignored so upgrades do not overwrite your changes.

Two ways to define sets:
- Declarative types (mapped to existing builder functions)
- Raw specs (full control for complex cases)

Example (declarative):
```json
{
  "version": 1,
  "capture_sets": [
    {
      "id": "HF_bands",
      "description": "Amateur radio HF bands (80m, 40m, 30m, 20m, 17m, 15m, 10m)",
      "type": "band_specs",
      "params": {
        "band_ids": ["80", "40", "30", "20", "17", "15", "10"],
        "suffix": "m"
      }
    },
    {
      "id": "HF_full",
      "description": "Complete HF coverage 0-30 MHz in 2 MHz steps (best with 2.4 MHz bandwidth)",
      "type": "step_specs",
      "params": {
        "start_mhz": 1,
        "end_mhz": 29,
        "step_mhz": 2,
        "suffix": " MHz",
        "crop_to_step": true,
        "crop_margin_khz": 5
      }
    }
  ]
}
```

Example (raw specs):
```json
{
  "version": 1,
  "capture_sets": [
    {
      "id": "custom_complex",
      "description": "Custom frequency configuration with manual specs",
      "type": "raw_specs",
      "specs": [
        {
          "spec_index": 0,
          "id": "145 MHz",
          "freq": 145000,
          "freq_range": {
            "id": "145 MHz",
            "freq_start": 144000,
            "freq_end": 146000,
            "crop_margin_khz": 10
          }
        }
      ]
    }
  ]
}
```

Steps:
1. Edit `capture_sets.json`
2. Restart the application
3. Select your set in the web interface

#### Capture Set Parameters

- **id**: Unique identifier for the capture set
- **start_mhz/end_mhz**: Frequency range in MHz
- **step_mhz**: Step size between capture frequencies
- **suffix**: Display suffix for frequency labels
- **crop_to_step**: Whether to crop recordings to step boundaries
- **crop_margin_khz**: Margin in kHz for frequency cropping

#### Important Notes

- **Output Directory**: When changing capture set specifications, start with a fresh output directory (rename/delete existing) to prevent empty image grid / csv columns
- **Center Frequency**: All frequencies are interpreted as center frequencies
- **Overlap**: It can be useful to have some overlap between frequency segments for better coverage


### Default SDR settings

- RTL-SDR: RF gain default 0 dB; bandwidth default 2400 kHz; IF gain not applicable
- SDRplay (RSP1A): RF gain default -18 dB; IF gain default -40 dB; bandwidth default 6000 kHz

Note: If you already have a config.json, delete it to adopt these new defaults.
