# qrm-logger



A software-defined radio (SDR) application for monitoring and logging radio frequency interference in amateur radio bands, based on GNU Radio.


> Both QRM, “Are you being interfered with?” and QRN, “Are the atmospherics strong?” are still common abbreviations used in Amateur Radio. Today, QRM stands for human-made noise, as opposed to QRN, which indicates noise from natural sources. If you hear an operator say, “I’m getting some QRM,” it means there’s man-made interference affecting your transmission.
[**](https://www.onallbands.com/word-of-the-day-qrm-what-is-qrm-in-ham-radio)

### Purpose of this application

Periodic broadband QRM that appears at random times is particularly challenging to identify and locate, especially on the shortwave bands.
Sometimes it helps to determine the timing of the QRM to infer its source.

This tool lets you record the spectrum (either manually or at periodic intervals) and create image grids for easy analysis.
It also generates RMS CSV files for further analysis.

- Optimized for Raspberry Pi (Linux); also works on Windows and macOS
- SDR support out of the box: RTL‑SDR v4 and SDRplay RSP1A (requires a 3rd‑party driver compilation step)
- Python 3.10+; requires conda/mamba with the conda‑forge channel.


**Architecture:**
- **Backend**: Python application using GNU Radio for SDR processing
- **Frontend**: Alpine.js single-page application served by the Python backend
- **Dependencies**: All frontend dependencies are included via CDN - no npm/node required
- **Installation**: Simply install the conda environment and run `python main.py`


### Usage Instructions & Application Screenshots:

For a detailed application description, usage instructions and screenshots check my web page:
### [https://do1zl.net/qrm-logger](https://do1zl.net/qrm-logger)



## Installation 

qrm-logger is ready to run after installing the conda environment - **no build step required**.


**System Requirements:**
- **Python**: 3.10 or higher (conda required)
- **Operating System**: Windows, Linux, macOS
- **SDR Hardware**: RTL-SDR v4 (or GNU Radio compatible devices)


### Get the code

```bash
git clone https://github.com/do1zl/qrm-logger
cd qrm-logger
```

**Alternative:** If you don't want to install git - go to the ```<> Code``` dropdown on top of this page and and choose 'Download ZIP'

### Install conda package manager

You need a conda package manager like [Miniforge](https://github.com/conda-forge/miniforge) or [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install) in order to install the dependencies of the application.
**Miniforge is preferred** because it uses conda-forge as the default channel.
You can also try [micromamba](https://github.com/mamba-org/micromamba-releases) for a minimal install.

The regular python install from the App Store is **not sufficient** to run the application! 


**Windows:** 
- Install [Miniforge](https://github.com/conda-forge/miniforge). Recommended install settings: Install for "Just me". Default Location. Options: Check "Create start menu shortcuts". Uncheck "Add miniforge3 to path". Uncheck "Register Miniforge3 as my default Python".
- Open "Miniforge Prompt" from start menu. You will see a prompt prefix ```(base)```

**Linux:**
- Install [Miniforge](https://github.com/conda-forge/miniforge)
- The installer will ask whether to enable automatic shell activation. Recommendation: choose 'yes', then disable automatic base environment activation as suggested there. Also see [here](https://linsnotes.com/posts/miniconda-installation-on-linux-should-you-enable-auto-initialization/)

**Mac:**
- Install miniconda or miniforge using brew, or use the download.
- See this [brew](https://formulae.brew.sh/cask/miniconda). Make sure to run the described steps to initialize your shell. Also see [here](https://naolin.medium.com/conda-on-m1-mac-with-miniforge-bbc4e3924f2b)




### Create environment and install dependencies

A conda environment stores all the dependencies required for the application. 
Read more about conda [here](https://docs.conda.io/en/latest/).

The following steps use `mamba` for the CLI commands. You can substitute this command with `conda` in case you are running miniconda. Mamba is a replacement conda package manager, both use the same command line syntax.

**Important:** You must execute these commands from a conda shell. 
A conda shell always displays a prompt prefix like ```(base)```. 
If you cannot see this prefix in your terminal, check 'Install conda package manager' section again.


```
# Important: You must execute these commands from a conda shell

# Go to the project directory
cd qrm-logger

# Create environment from environment.yml file
# This will create 'qrm-logger' environment and install all required packages 
mamba env create -f environment.yml

# or choose a different environment name (optional)
# mamba env create -f environment.yml -n qrm1

# Activate the environment. Your prompt prefix will change to (qrm-logger)
mamba activate qrm-logger

# Check installed packages (optional)
mamba list

# List existing environments (optional)
mamba env list

```



## Usage


### Starting the Application
```
# Activate environment
mamba activate qrm-logger

# Start the application (web interface)
python main.py

# OR: Record once and exit (no web interface)
# python main.py --run-once
```


### Access Web Interface
- Navigate to `http://localhost:7060` in your web browser



## Hardware Compatibility

### Tested Devices
The application can be adapted to all devices supported by GNU Radio. 
Currently, only **RTL-SDR** is supported out-of-the-box, but it should be easy to integrate other SDRs supported by GNU Radio.



| Device name        | package     | Remarks                                                                                                                                                 |
|--------------------|-------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| RTL-SDR v4         | `gr‑osmosdr`  | Tested on Windows 11 and Raspberry Pi OS                                                                                                                 |
| RTL-SDR (other)    | `gr‑osmosdr`  | Not tested yet - but should work out-of-the-box                                                                                                         |
| SDRplay&nbsp;RSP1A | `gr‑sdrplay3` | Tested on Raspberry Pi OS. Package is **not** available in conda-forge and requires compilation of a 3rd-party driver. See [here](docs/sdrplay_notes.md) |


 See [sdr_support.md](docs/sdr_support.md) for information on how to add support for other devices.

## Configuration



### Web Server Configuration

By default, the web interface is configured for local access only (`localhost:7060`). This is the most secure option as it prevents network access from other devices.
Change `web_server_host` in `config/web_server.py` to `0.0.0.0` to allow access from other devices on your network. Only use this on trusted networks since there is no authentication.


### Running as a Service on Raspberry Pi

For headless 24/7 monitoring on Raspberry Pi, qrm-logger includes pre-configured systemd service files for easy installation.
See [service_install.md](docs/service_install.md) 


## Additional documentation
### RMS

[rms.md](docs/rms.md)

### Output Files


[output_files.md](docs/output_files.md)



### General configuration

[configuration.md](docs/configuration.md) 


### Troubleshooting

[troubleshooting.md](docs/troubleshooting.md) 


## Open Issues & Future Ideas

I am still pretty new to the world of SDR programming with gnu-radio. There might be potential to improve certain data handling & FFT calculations in the application.



## Credits

### Primary Resources
- **PySDR: A Guide to SDR and DSP using Python** ([pysdr.org](https://pysdr.org)) - Primary reference for SDR concepts and implementation
  - Online textbook providing foundational knowledge for software-defined radio programming
  - Essential resource for understanding DSP fundamentals and GNU Radio workflows

### AI Contributions
- **Claude 4 Sonnet (Anthropic)** via [Warp.dev](https://warp.dev) - Assisted with code refactoring, documentation improvements, and technical problem-solving
- **Development Note:** Most of the application was created without AI assistance in the previous year. Claude has been recently introduced to help clean up code, refactor existing functionality, and implement new features. The results are quite impressive imho.

### Software Dependencies
- **GNU Radio** - Core signal processing framework
- **gr-osmosdr** - Hardware abstraction layer for SDR devices
- **NumPy** - Numerical processing and data manipulation
- **Matplotlib** - Spectrum visualization and plotting
- **Bottle** - Lightweight Python web framework
- **Waitress** - Lightweight Python HTTP server
- **APScheduler** - In-process job scheduling


#### CDN Dependencies (frontend)
- **Alpine.js** - Reactive web interface framework
- **Bulma CSS** - Modern CSS framework for UI styling
- **Panzoom** - Interactive image zoom functionality
- **PhotoSwipe** - Image gallery and lightbox with preloading
- **iziToast** - Notifications
- **cRonstrue** - Human-readable descriptions for cron expressions
