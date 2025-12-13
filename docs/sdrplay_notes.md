# SDRPLAY notes

## How to compile SDRplay module


It was disappointing to learn that there are no official prebuild SDRplay drivers available for GNU Radio.

There is an 3rd-party driver [available](https://github.com/fventuri/gr-sdrplay3),
however the binary is neither available in conda-forge nor in radioconda (apparently due to license reasons). _("Basically, because of the proprietary license of the SDRPlay API, I am afraid it is not possible to use conda-forge for this GNU Radio OOT module like all the other ones.")_[ [*] ](https://github.com/fventuri/gr-sdrplay3/issues/57#issuecomment-2829297851)

## gr-sdrplay3


Get the driver [here](https://github.com/fventuri/gr-sdrplay3).
It supports the following SDRplay devices:

```
    RSP1
    RSP1A
    RSP1B
    RSP2
    RSPduo (all modes of operation)
    RSPdx
    RSPdx-R2
```

I tested it with the RSP1A device (will be used in qrm-logger by default). 

To use a different model, change the following line in 
`sdr/sdr_sdrplay.py` inside the qrm-logger source:

```
    sdrplay3_rsp_0 = sdrplay3.rsp1a("", stream_args = args)
```



## Linux

I was able to compile on linux with these dependencies:

- Raspberry Pi OS 64 Bit (bookworm)
- Miniforge
- GNU Radio 3.10.12.0 
- Python 3.13.5
- SDRplay API 3.15
- SDRplay RSP1A


Steps:

1. Install build dependencies into environment:
```
mamba activate qrm-logger

mamba install gnuradio-build-deps
```

2. Follow the linux compile instructions in the gr-sdrplay3 project. 
**It is important** to run the compilation inside the qrm-logger environment so it uses the matching python version. 

3. There are two files being created in the _make install_ step :


```
-- Installing: /usr/local/lib/python3.13/site-packages/gnuradio/sdrplay3/__init__.py
-- Installing: /usr/local/lib/python3.13/site-packages/gnuradio/sdrplay3/sdrplay3_python.cpython-313-aarch64-linux-gnu.so
```

3. Copy these two files into your conda environment:

```
cp -r /usr/local/lib/python3.13/site-packages/gnuradio/sdrplay3/ ~/miniforge3/envs/qrm-logger/lib/python3.13/site-packages/gnuradio/sdrplay3
```

## Windows

**Note**: For windows, see [issue #57](https://github.com/fventuri/gr-sdrplay3/issues/57) for details. I was unable to compile the driver under Windows. Since I run the application on linux, I don't care.

## Configure qrm-logger

After successful compilation you must configure qrm-logger to use the device.
Edit 
`config/sdr_hardware.py` in the qrm-logger source:

```
device_name = DEVICE_NAME_SDRPLAY
```
Then delete the config-dynamic.json file to have it recreated on startup. Start the application and configure the device in UI config tab 'SDR'.

## Remarks

I cam across some problems / specific behaviour when using SDRplay.


### Gain settings
**IMPORTANT** 
make sure to use correct (negative) values, otherwise device will not start!

The current implementation of qrm-logger allows both RF gain and IF gain to be user-configurable. Default values: RF gain = -18 dB, IF gain = -40 dB, Bandwidth = 6000 kHz.

> In this gr-sdrplay3 module, the two gain parameters (IF and RF) are indeed gains, i.e. higher values mean higher signal gain (or less attenuation, if you prefer to look at it that way).
> Since the SDRplay RSP family of devices 'thinks' in terms of 'gain reduction' (i.e. attenuation), the values you want to assign to the IF and RF gain are always negative: for instance the IF gain goes from -20 (highest signal gain) to -59 (lowest signal gain); similarly the gain values for the RF gain go from 0 (highest signal gain of the RF chain) to -N, where the value of N depends on the specific RSP device and frequency band, as per the 'Gain Reduction Tables' in the SDRplay API Specification guide (https://www.sdrplay.com/docs/SDRplay_API_Specification_v3.09.pdf) on page 38.
> Please note that all the gain values in the set_gain() methods are in dB.

https://github.com/fventuri/gr-sdrplay3/issues/20

### Bandwidth settings

Regarding bandwidth settings:
> "You will see some attenuation of the signal outside of the IF bandwidth"
> 
https://www.sdrplay.com/community/viewtopic.php?f=7&t=4520


