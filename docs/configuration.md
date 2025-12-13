

## Configuration

qrm-logger uses a three-tier configuration system that separates static defaults, band definitions, and runtime settings:

### Configuration Architecture

**1. Static Configuration (`config-static.toml`)**
- User-editable TOML file at project root containing default values
- Auto-generated on first run with sensible defaults and inline documentation
- Organized into logical sections:
  - `[analysis]` - Frequency exclusion settings
  - `[paths]` - Output directory and file retention
  - `[recording]` / `[recording.fft]` - Recording and FFT parameters
  - `[scheduler]` - Automated recording schedule
  - `[sdr]` - SDR device configuration
  - `[visualization]` / `[visualization.grid]` - Plot and grid settings
  - `[web]` - Web server host/port
- Changes require application restart
- File is git-ignored so upgrades don't overwrite your customizations

**2. Band Definitions (`config-bandplan.toml`)**
- User-editable TOML file defining amateur radio band markers
- Auto-generated on first run with IARU Region 1 defaults
- Simple structure: `[band_id]` sections with `start_khz` and `end_khz`
- Includes HF bands (160m-10m) and VHF/UHF services
- Region 2 variants included as comments for easy customization
- Changes require application restart
- File is git-ignored

**3. Capture Sets (`config-capture_sets.json`)**
- Defines frequency ranges and monitoring strategies
- Auto-generated on first run with default HF/VHF/UHF sets
- References band IDs from `bands.toml` for band-based monitoring
- Supports declarative (band_specs, step_specs) and raw spec formats
- Changes require application restart
- File is git-ignored

**4. Dynamic Configuration (`config-dynamic.json`)**
- Runtime-adjustable parameters managed by the web interface
- Contains settings that can change during operation:
  - `rf_gain`, `if_gain` - SDR gain settings
  - `sdr_bandwidth` - Current bandwidth
  - `rec_time_default_sec` - Recording duration
  - `scheduler_cron`, `scheduler_autostart` - Schedule settings
  - `fft_size`, `min_db`, `max_db` - FFT parameters
  - `capture_sets_enabled` - Active capture sets
- Modified through the web interface without restarting
- Persists settings between sessions
- Auto-generated from `config-static.toml` defaults on first run

### Getting Started

1. **First Run**: Start the application - it will auto-generate `config-static.toml` and `config-bandplan.toml` with defaults
2. **Customize Defaults**: Edit `config-static.toml` and `config-bandplan.toml` to match your setup (optional)
3. **Restart**: Restart the application to load your customizations
4. **Runtime Adjustments**: Use the web interface to fine-tune operational parameters

### Editing Configuration Files

**config-static.toml**
- Edit with any text editor
- Includes inline comments explaining each setting
- Changes take effect after application restart
- To reset to defaults: delete the file and restart

**config-bandplan.toml**
- Edit to customize band definitions for your region
- Simple format: band ID as section header, frequencies in kHz
- Example:
  ```toml
  [80m]
  description = "80 meter band (3.5 MHz)"
  start_khz = 3500
  end_khz = 3800
  ```
- Band IDs must match those referenced in `config-capture_sets.json`
- To reset to defaults: delete the file and restart

### Capture Sets

Capture sets define the frequency ranges that qrm-logger will monitor. The system uses a two-file approach:
- **`config-bandplan.toml`** - Defines band frequency ranges (e.g., 80m: 3500-3800 kHz)
- **`config-capture_sets.json`** - References bands and defines capture strategies

#### Built-in Capture Sets

**HF_bands**
- Monitors specific amateur radio HF bands: 80m, 40m, 30m, 20m, 17m, 15m, 10m
- References band definitions from `config-bandplan.toml`
- Uses band-specific center frequencies optimized for amateur radio activity
- Ideal for focused monitoring of ham radio frequencies

**HF_full** 
- Comprehensive HF coverage from 0-30 MHz in 2 MHz steps
- **Best used with 2.4 MHz bandwidth setting**
- Uses frequency cropping to avoid FFT problems at band edges
- Provides complete HF spectrum coverage with good resolution
- Works with most SDR devices

**HF_full_wide**
- Wideband HF coverage from 3-30 MHz in 5 MHz steps
- **Best used with 6 MHz bandwidth setting**
- Uses frequency cropping to avoid FFT problems at band edges
- Optimized for high bandwidth SDRs that support wider spans
- More efficient capture for wideband-capable SDRs

#### Configuration Files

**config-bandplan.toml** (Band Definitions)
- Defines frequency ranges for amateur radio bands
- Auto-generated on first run with IARU Region 1 defaults
- Simple structure: section per band with start/end frequencies
- Edit to customize for your region or add custom bands

Example:
```toml
[80m]
description = "80 meter band (3.5 MHz)"
start_khz = 3500
end_khz = 3800

[40m]
description = "40 meter band (7 MHz)"
start_khz = 7000
end_khz = 7200
```

**config-capture_sets.json** (Capture Strategies)
- References band IDs from `config-bandplan.toml` to build capture sets
- Auto-generated on first run with sensible defaults
- Git-ignored so upgrades don't overwrite your changes
- Supports three types: `band_specs`, `step_specs`, `raw_specs`
- See [capture_sets_example.json](capture_sets_example.json) for complete examples

#### Customization Workflow

**To add a custom band:**
1. Edit `config-bandplan.toml` and add your band:
   ```toml
   [6m]
   description = "6 meter band (50 MHz)"
   start_khz = 50000
   end_khz = 54000
   ```
2. Edit `config-capture_sets.json` to reference it:
   ```json
   {
     "id": "My_Bands",
     "type": "band_specs",
     "params": {
       "band_ids": ["80m", "40m", "6m"]
     }
   }
   ```
3. Restart the application
4. Select your capture set in the web interface

**To modify existing bands:**
1. Edit `config-bandplan.toml` (e.g., change 80m for Region 2: `end_khz = 4000`)
2. Restart the application
3. Your capture sets automatically use the new frequencies

#### Important Notes

- **Output Directory**: When changing capture set specifications, start with a fresh output directory (rename/delete existing) to prevent empty image grid / csv columns
- **Center Frequency**: All frequencies are interpreted as center frequencies
- **Overlap**: It can be useful to have some overlap between frequency segments for better coverage
- **Band IDs**: Must match between `config-bandplan.toml` and `config-capture_sets.json` (e.g., `80m`, `40m`)


### Default SDR settings

- RTL-SDR: RF gain default 0 dB; bandwidth default 2400 kHz; IF gain not applicable
- SDRplay (RSP1A): RF gain default -18 dB; IF gain default -40 dB; bandwidth default 6000 kHz

Note: If you already have a config-dynamic.json, delete it to adopt these new defaults.
