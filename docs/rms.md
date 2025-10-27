
## RMS Analysis

QRM Logger includes advanced RMS (Root Mean Square) analysis capabilities to help identify and characterize different types of radio frequency interference. This feature provides quantitative measurements that complement the visual spectrum analysis.

### Overview

The RMS analysis system calculates interference levels across frequency ranges and provides both standard and truncated measurements. This dual approach helps distinguish between broadband noise and narrowband interference sources, making it easier to identify and locate QRM sources.

Note: For RMS, only the core frequency window of each capture spec is used - crop margins are excluded. Additionally, known artifact frequencies defined in config/analysis.py as exclude_freqs_khz (e.g., 0.0 kHz, 28800.0 kHz) are excluded from the calculation.

### UI Features

**Web Interface Integration:**
- **CSV Data View**: Switch to CSV mode in the web interface to view RMS data tables
- **Raw vs Delta Values**: Toggle between absolute RMS values and delta changes between recordings
- **Data Type Selection**: Choose between Standard RMS (all signals) and Truncated RMS (strong signals capped)
- **Configurable Color Coding**: Adjust threshold levels for visual interference level indication
- **Threshold Configuration**: Adjust medium, high, and critical interference thresholds via web interface


### RMS Calculation Details

QRM Logger provides two types of RMS measurements to help identify different types of interference:

#### Standard RMS Calculation
- **Linear Domain Processing**: Converts dB values to linear power scale before RMS calculation for physically meaningful results
- **SDR Artifact Exclusion**: Automatically excludes ±3 kHz around 0 Hz to avoid contamination from SDR hardware artifacts
- **Normalization**: Values scaled to 0-100% based on configured dB range (`min_db` to `max_db`)
- **Negative Value Prevention**: Results are clamped to prevent negative values while allowing >100% for very strong signals

#### Truncated RMS Calculation
- **Signal Capping**: Caps the strongest 5% of signals to the 95th percentile threshold in linear power domain
- **Interference Robustness**: Provides measurements less affected by strong narrowband interference
- **Comparative Analysis**: Large differences between standard and truncated RMS suggest narrowband interference presence
- **Same Processing**: Uses identical normalization and artifact exclusion as standard RMS

#### Interpreting RMS Values

**Standard RMS Value Ranges:**
- **0-20%**: Typical noise floor or very weak signals
- **20-60%**: Moderate RF activity, possible weak interference  
- **60-100%**: Strong signals within expected dB range
- **>100%**: Very strong signals exceeding configured maximum dB level

**Truncated RMS Value Ranges:**
- **0-15%**: Clean noise floor with minimal strong signal contamination
- **15-45%**: Moderate broadband activity with strong signals capped
- **45-80%**: High broadband interference levels (strong signals limited)
- **>80%**: Very high broadband interference even after signal capping

**Truncated RMS Analysis:**
- **Similar to Standard**: When truncated RMS ≈ standard RMS (difference <15%), suggests uniform or broadband interference
- **Lower than Standard**: When truncated RMS << standard RMS (difference >15%), suggests narrowband interference dominance
- **Value Ranges**: Truncated RMS typically shows lower values than standard RMS when strong peaks are present

**Practical Usage Guidelines:**
- Use **standard RMS** for overall RF activity level assessment
- Use **truncated RMS** for baseline interference levels less affected by strong signals
- **Cross-Reference**: Correlate RMS spikes with visual spectrum plots for detailed interference characterization


