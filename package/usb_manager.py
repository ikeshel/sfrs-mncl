#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__version__    = "3.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
1) pip3 install pyserial
    python -m serial.tools.list_ports -v
    pyserial-ports -v

2) Access to USB
    sudo adduser <irakli> dialout
    groups; sudo reboot; groups

3) Test
    pyserial-miniterm /dev/ttyACM0 115200
'''

import serial
import serial.tools.list_ports

from loguru import logger 

###############################################################################
###############################################################################
###############################################################################
class UsbManager:
    '''USB Manager class to handle USB device connections.'''

    #==========================================================================
    def __init__(self, device_id=None):
        '''Initialize the USB Manager.'''

        # logger.remove()
        # logger.add( sys.stderr, 
        #             # level="DEBUG",
        #             format="{time:HH:mm:ss}|{level: <8}| {message}")
        logger.debug(f"UsbManager.__init__() {self.__class__.__name__}")
        logger.debug(f"UsbManager.__init__() {self.__class__.__module__}")

        self.device_id         = device_id
        self.device_path       = None
        self.serial_connection = None

        if device_id:
            self.find_port(self.device_id)
            self.connect()

    #==========================================================================
    def __del__(self):
        '''Destructor to clean up resources.'''
        print('Destructor called!')
        if self.serial_connection is not None:
            print(f"Closing USB port: {self.device_path}")
            self.serial_connection.flush()
            self.serial_connection.close()

    #==========================================================================
    def find_port(self, device_id):
        '''Find the specified port and set the device path.'''
        for _, (port_name, description, hardware_id) in enumerate(sorted(serial.tools.list_ports.comports())):
            if device_id in hardware_id:
                logger.debug(f'Port Name:   {port_name}')
                logger.debug(f'Description: {description}')
                logger.debug(f'Hardware ID: {hardware_id}')
                self.device_path = port_name
                return True
        return False

    #==========================================================================
    def connect(self, baud_rate=9600, timeout=5) -> bool:
        '''Connect to the selected device.'''
        if not self.device_path:
            logger.error('No device specified to connect.')
            return False
        
        try:
            # self.serial_connection = serial.Serial(   port=self.device, 
            #                             baudrate=brate, 
            #                             # bytesize=8, 
            #                             # parity='N', 
            #                             # stopbits=1, 
            #                             timeout=timeo,
            #                             # xonxoff=False, 
            #                             # rtscts=False, 
            #                             # dsrdtr=False
            #                             )
            self.serial_connection = serial.Serial(
                port=self.device_path, 
                baudrate=baud_rate, 
                timeout=timeout
            )
            logger.debug(f"Connected to USB port: {self.device_path}")
            return True
        except Exception as e:
            logger.error(f'Failed to connect to USB device: {e}')
            logger.error('Run the following commands for debugging:')
            logger.error('python -m serial.tools.list_ports -v')
            logger.error('pyserial-ports -v')
            logger.error('lsusb and lsusb -v -d vendor (0aad:0117)')
            self.serial_connection = None
            return False

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == '__main__':
    my_usb_dev = UsbManager()

    print(my_usb_dev.find_port( 'VCP109499' ))
    
    print(my_usb_dev.connect())
