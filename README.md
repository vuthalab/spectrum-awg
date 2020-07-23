# Spectrum M4i.6622-x8 Library
This software is for controlling the M4i.6622-x8 Arbitrary Waveform Generator (AWG) from Spectrum in Python. The code allows you to
pass in any function of your choosing and have the AWG produce the corresponding waveform.

## Getting Started 
First, follow the installation procedures to install the necessary drivers, then clone a copy of this repo.

### Prerequisites
When using this code, numpy is the only other library required, all others required libraries are included in this repository. To install numpy, use:
```
pip install numpy
```


# M4i.6622 Installation Procedure
### Ubuntu 18.04 or 20.04:
The installation on an Ubuntu desktop is fairly straightforward if you are using Linux Kernel 4.15.0-20-generic on 18.04. If so, you only need to install the Linux driver from Spectrum’s driver list and reboot the computer.

If you are using any other Linux version or Kernel, things get a bit more complicated; you will need to get the Linux Kernel Driver Module associated to the OS being used and then compile it yourself (See resources section below).

After getting a hold of the kernel driver module, cd into the directory and use:
```
chmod +x make_spcm_linux_kerneldrv.sh 
```
to compile the make file.

Then run:
``` 
./make_spcm_linux_kerneldrv.sh
```
to run the installer.

Reboot the PC and check if the card shows up when running:
```
ls /dev
```
and check for spcm0 or spcm1. If they aren’t found, power off the computer and try placing the card in properly or switch PCIe lanes. Check if the riser card is well plugged in and powered.

After seeing spcm0 or spcm1 in ls /dev, run:
```
dmesg | grep -iC 3 "spcm"
```
If no errors show up, then the card is ready. Clone the M4i6622 library from the lab Github and run testing.py. If it all works, there should be 2 sine waves outputted from Channels 0 and 1.

However if AMD-Vi logs an IO_PAGE_FAULT (you can see this when running the above dmesg command after trying testing.py), edit the bootloader by running the following lines:
```
sudo nano /etc/default/grub
```
Then change the line that starts with GRUB_CMDLINE_LINUX to include:
```
GRUB_CMDLINE_LINUX="iommu=soft"
```
After that, update the grub with:
```
sudo update-grub
```
Restart the computer and it should work fine. If not, try:
```
GRUB_CMDLINE_LINUX="iommu=off"
```
instead of iommu=soft.

### Windows 7/8/10
Fortunately, if you are using Windows, the entire process is very simple (at least in my experience). You only need to install the Win 7/8/10 Driver from Spectrum’s Driver list, see the ressources section below. Follow the on-screen instructions and then reboot the computer. After that, the card should show up on “Device Manager”.

### Additional and Useful Resources
Kernel: Submit an NDA to Spectrum (by first making a support request to receive an NDA) to receive the kernel.
Manual: [M4i.66xx Manual](https://spectrum-instrumentation.com/sites/default/files/download/m4i_m4x_66xx_manual_english.pdf)
Drivers: [Drivers List](https://spectrum-instrumentation.com/en/downloads/drivers)

# Installing the Repo:
To install the repo, simply download this repo on Github, or clone this repo using the git clone command.


# Using the repo to control the M4i.6622-x8 card
With this repo, controlling the outputs of the M4i.6622 is very simple:

```python
M4i = M4i6622(channelNum=4,sampleRate=625)
r = M4i.setSoftwareBuffer()

print("Software Buffer Status:",str(r))

M4i.setupCard( (f0,f1,f2) )
M4i.startCard()
r = M4i.stop()

print("Status:",str(r))
```
### General Procedure
The procedure follows these general steps:
1. Initialize the M4i6622 object that will be used to interface with the card.
2. Set the software buffer.
3. Set up the card and populate the buffer with the chosen functions.
4. Starting the card.
5. Stopping the card when finished.

### Guidelines for Functions

##### Defining Functions
The functions used in this code have to be defined using numpy functions and must be integers. An example for a sine function is:
``` python
def sin(x,f=1):
    return np.floor(6000*np.sin(np.multiply(2*math.pi*f/SAMPLES,x)))
```
Examples of functions can be found in the functions.py script in the Functions folder.

##### Limits of the AWG
The AWG operates at a maximum sampling rate of 625 MegaSamples per second, hence by the Nyquist-Shannon Sampling theorem can only output a sine wave with a frequency less than or equal to 312.5 MHz. It is also important to note that the AWG can only output voltages from -2.5V to +2.5V.

##### Defining less functions
Defining less functions than the required amount (amount of channels) will automatically set all the other ones to 0.

### Parameters of the M4i6622 class

##### Address
The address of the M4i card, by default should be at /dev/spcm0, if there is no other Spectrum card installed on the machine.

##### Number of Channels (channelNum)
The number of channels to be used. It can only be 1,2 or 4. This dictates how the buffer is formed. The default is 4 channels.

##### Sample Rate
This is the sample rate of the card in Mega Samples per second. The M4i.6622's maximum is of 625 Mega Samples per second. This is the default,

##### Reference Clock
This parameter is to flag whether or not the card should use a reference clock instead of its own crystal oscillator. The default is False, no reference clock is expected to be attached. 

##### Reference Clock Frequency
This parameter is only used when the reference clock is being used (the reference clock flag is True). This parameter is to be set to the frequency in hertz of the reference clock. By default it is set to 10 MHz. Reference clock frequencies can only go from 10 MHz to 1.25GHz, but cannot be between 750 to 757 MHz and 1125 to 1145 MHz.

##### Clock Output (clockOut)
This parameter sets whether or not the the M4i.6622 will output its internal clock. By default it's set to False.



# Authors and Contributors
Amar Vutha, Mingde Yin, Ryan Zazo

# License
This project is licensed under the MIT License - see the LICENSE.md file for details

# Acknowledgments
This code has been based on Spectrum's Example: simple_rep_single.py