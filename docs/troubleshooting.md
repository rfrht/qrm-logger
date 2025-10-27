
### Common Issues

#### SDR Device Not Detected

You should see this output when starting a record process:
```bash
Using device #0 RTLSDRBlog Blog V4 SN: 00000001
Found Rafael Micro R828D tuner
RTL-SDR Blog V4 Detected
```
Windows: make sure to install the RTL-SDR v4 drivers via Zadig.

#### Windows: Application quits when initializing the SDR
I observed this behaviour a few times with RTLSDR on Windows. The application silently exits after this output:

```
gr-osmosdr 0.2.0.0 (0.2.0) gnuradio 3.10.12.0
built-in source types: file rtl rtl_tcp uhd miri hackrf bladerf airspy airspyhf soapy redpitaya
[INFO] [UHD] Win32; Microsoft Visual C++ version 14.2; Boost_108600; UHD_4.8.0.0-release
```

This never happens on Raspberry Pi Linux. Not sure about the reason. You can try disabling `sdr_shutdown_after_recording` (keep SDR running between recordings) and see if it helps.


#### Application crashes with OutOfMemory Error

Each frequency slice is recorded in memory and written to disk after recording is completed. 
This is to prevent performance problems on computers with slow IO. Reduce recording time and / or FFT size.


#### Web Interface Not Accessible
- Ensure no firewall is blocking port 7060
- Check if the application started successfully in the terminal
- Try accessing `http://127.0.0.1:7060` instead of localhost


#### Performance Issues
- Reduce FFT size via the web interface for faster processing
- Lower the span or recording time for less CPU usage
