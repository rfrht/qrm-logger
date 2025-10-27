## Extending qrm-logger

### Additional Device Support


gnuradio-osmosdr has built-in support for many popular devices, so it should be possible to add those without any additional dependencies:
```
gr-osmosdr 0.2.0.0 (0.2.0) gnuradio 3.10.12.0
built-in source types: file rtl rtl_tcp uhd miri hackrf bladerf airspy airspyhf soapy redpitaya
```

Check the [documentation](https://osmocom.org/projects/gr-osmosdr/wiki)
and try to change the following line in 
`sdr/sdr_rtlsdr.py` inside the qrm-logger source to one of the source types in the list above:

```
    device_name = "rtl"
```

Also have a look at `sdr/sdr_factory.py` on how to add a new device.

List of devices supported by GnuRadio: https://wiki.gnuradio.org/index.php/Hardware



### About SDRplay support in GNU Radio
See [sdrplay_notes](sdrplay_notes.md) for more information.

