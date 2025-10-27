
## Output Files

**⚠️ Output Directory Configuration**: By default all output files are stored in `./_recordings/` (relative to the application directory). You can change this location by editing the `output_directory` setting in `config/output_directories.py` before running the application. Choose a location with sufficient disk space as recordings can accumulate several GB over time.

QRM Logger generates multiple types of output files organized in a structured directory hierarchy:


### Directory Structure
```
_recordings/
├── counter.txt                           # Recording sequence counter (global)
└── <CAPTURE_SET_ID>/
    ├── plots_full/                       # Full-resolution spectrum plots
    │   └── <YYYY-MM-DD>/
    │       └── plot-*.png
    ├── plots_resized/                    # Thumbnail plots for grid generation
    │   └── <YYYY-MM-DD>/
    │       └── plot-*.png
    ├── grids_full/                       # Combined time-series grid images
    │   └── <CAPTURE_SET_ID>_grid_<YYYY-MM-DD>_[<LABEL>]_full.png
    ├── grids_resized/                    # Resized grid images for UI
    │   └── <CAPTURE_SET_ID>_grid_<YYYY-MM-DD>_[<LABEL>]_resized.png
    ├── csv/                              # CSV data export (RMS)
    │   ├── rms_standard.csv
    │   └── rms_truncated.csv
    ├── log/                              # Processing logs
    │   └── log.csv
    ├── metadata/                         # Plot metadata and recording details
    │   └── <YYYY-MM-DD>/
    │       └── plots_metadata.csv
    └── raw/                              # Compressed FFT data (optional)
        └── <YYYY-MM-DD>/
            └── fft-<id>-<counter>.raw
```

### File Types

**Spectrum Plots** (`./_recordings/<CAPTURE_SET_ID>/plots_*/<YYYY-MM-DD>/`)
- **Content**: Waterfall plots showing frequency vs time with band markers
- **Format**: PNG images
- **Naming**: `plot_[container]_[date]_[time]_[counter]_[capture-id].png`

**Grid Images** (`./_recordings/<CAPTURE_SET_ID>/grids_*/`)
- **Content**: Combined time-series view of all frequency segments
- **Format**: PNG with both full-size and resized versions
- **Naming**: `[container]_grid_[date]_full.png` and `[container]_grid_[date]_resized.png`

**CSV Data** (`./_recordings/<CAPTURE_SET_ID>/csv/`)
- **Standard RMS Data**: `rms_standard.csv` - Traditional RMS values including all frequency bins
- **Truncated RMS Data**: `rms_truncated.csv` - RMS values with strongest 5% of signals capped


**Metadata** (`./_recordings/<CAPTURE_SET_ID>/metadata/<YYYY-MM-DD>/`)
- **Plot Metadata**: `plots_metadata.csv` - Recording details, notes, and file references
- **Purpose**: Used by grid generation algorithm to organize and annotate images


**Raw FFT Data** (`./_recordings/<CAPTURE_SET_ID>/raw/<YYYY-MM-DD>/`)
- **Format**: Compressed binary files containing raw spectrum data
- **Control**: Enabled/disabled via `keep_raw_files` setting
- **Storage**: Significant disk space - consider carefully for long-term monitoring


### Data Retention

No automatic deletion - files accumulate over time

**Storage Considerations**:
- Spectrum plots: ~200-500 KB per plot
- Grid images: ~5 - 150 MB per day
- Raw data: ~10-50 MB per recording session (if enabled)
- 24/7 monitoring can generate several GB per month

**Recommended Maintenance**:
- Monitor disk space regularly
- Archive or delete old data based on analysis needs

