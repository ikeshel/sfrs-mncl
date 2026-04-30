#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__version__    = "3.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
for testing:
    cd lib; python
    >import ST3_hmp4040
    >hmp = ST3_hmp4040.HMP4040("../config/asic_HMP4040.yaml")

TODOlist:
    - logging
    - all outputs simultaneusly
    https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/h/hmp_serie/HMPSeries_UserManual_en_02.pdf#page=83
    - 
    hmp.send_cmd('SYST:BEEP')
    hmp.send_cmd('SYST:LOC') # REM & MIX
    
'''

# --- Configure Logging -------------------------------------------------------
import sys
from loguru import logger 

from yaml_manager  import YamlManager
from usb_manager   import UsbManager

###############################################################################
###############################################################################
class Hmp4040(UsbManager):
    '''    
    '''

    Rcmnd = '' # read command container
    Wcmnd = '' # write command container
    Wrtrn = '' # return container

    hmp_dict= {'C1V': 0.0, 'C1A': 0.0, 'C2V': 0.0, 'C2A': 0.0, 'C3V': 0.0, 'C3A': 0.0, 'C4V': 0.0, 'C4A': 0.0}
       
    #==========================================================================
    def __init__(self, yaml=''):

        self.states   = [0,0,0,0]
        self.volts    = [0,0,0,0]
        self.currents = [0,0,0,0]
        self.values   = ['0','0','0','0', # V1,A1,V2,A2,V3,A3,V4,A4
                         '0','0','0','0']

        try:
            self.hmp_yaml = YamlManager( yaml ).yaml_dict
        except:
            logger.error(f"No '{yaml}' file found")
            raise FileNotFoundError('No yaml file found')
            return

        super().__init__(self.hmp_yaml['ID']) # call parent constructor

        # initialize device currents 'INST OUT1\nAPPL 2.65,1.7'
        command =   'INST OUT'+str(self.hmp_yaml['C1'])+\
                    '\nAPPL ' +str(self.hmp_yaml['V1'])+\
                    ','       +str(self.hmp_yaml['A1'])+\
                    '\n'+\
                    'INST OUT'+str(self.hmp_yaml['C2'])+\
                    '\nAPPL ' +str(self.hmp_yaml['V2'])+\
                    ','       +str(self.hmp_yaml['A2'])+\
                    '\n'+\
                    'INST OUT'+str(self.hmp_yaml['C3'])+\
                    '\nAPPL ' +str(self.hmp_yaml['V3'])+\
                    ','       +str(self.hmp_yaml['A3'])+\
                    '\n'+\
                    'INST OUT'+str(self.hmp_yaml['C4'])+\
                    '\nAPPL ' +str(self.hmp_yaml['V4'])+\
                    ','       +str(self.hmp_yaml['A4'])
        
        logger.debug( command )
        self.write_cmd( command )
        self.write_cmd('SYST:BEEP')

    #==========================================================================
    def __del__(self):
        print('Destructor called, USB connection closed.')
    
    #==========================================================================
    def identify(self):
        return self.send_cmd('*IDN?')

    #==========================================================================
    def hmp_beep(self):
        self.write_cmd('SYST:BEEP')

    #==========================================================================
    def send_cmd(self, cmd):
        '''command with return'''
        try:
            self.serial_connection.write(str.encode(cmd)+b"\r\n")
            return self.serial_connection.readline().decode().strip()
        except:
            logger.error(serial.serialutil.SerialException)
            logger.error('USB connection was lost')
            return ''

    #==========================================================================
    def write_cmd(self, cmd):
        '''command without return'''
        if self.serial_connection.closed:
            self.connect()
            logger.error('USB connection was lost')
        self.serial_connection.write(str.encode(cmd)+b"\r\n")


    #==========================================================================
    def gen_on(self):
        self.write_cmd("OUTPUT:GENERAL ON")

    #==========================================================================
    def gen_off(self):
        self.write_cmd("OUTPUT:GENERAL OFF")

    #==========================================================================
    def all_off(self):
        self.write_cmd( "INST OUT1\nOUTP:STATE 0\n"\
                        "INST OUT2\nOUTP:STATE 0\n"\
                        "INST OUT3\nOUTP:STATE 0\n"\
                        "INST OUT4\nOUTP:STATE 0\n"\
                        "OUTPUT:GENERAL OFF")

    #==========================================================================
    def all_on(self):
        self.write_cmd( "INST OUT1\nOUTP:STATE 1\n"\
                        "INST OUT2\nOUTP:STATE 1\n"\
                        "INST OUT3\nOUTP:STATE 1\n"\
                        "INST OUT4\nOUTP:STATE 1\n"\
                        "OUTPUT:GENERAL ON")

    #==========================================================================
    def ch_on(self, chs=[1,2,3,4]) -> None:
        logger.debug(f"Turning ON channels: {chs}")
        for ch in chs:
            self.write_cmd(f'INST OUT{str(ch)}\nOUTP:STATE 1')
            # self.Wcmnd = f'INST OUT{str(ch)}\nOUTP:STATE 1'
            # self.RunCommand()

    #==========================================================================
    def ch_off(self, chs=['4']) -> None:
        logger.debug(f"Turning OFF channels: {chs}")
        for ch in chs:
            self.write_cmd(f'INST OUT{str(ch)}\nOUTP:STATE 0')
            # self.Wcmnd = f'INST OUT{str(ch)}\nOUTP:STATE 0'
            # self.RunCommand()

    #==========================================================================
    def ch_states(self, chs=[1,2,3,4]) -> list:
        for ch in chs:
            ret = self.send_cmd(f"INST OUT{int(ch)}\nOUTP:STATE?")
            nn = int(ch)-1
            self.states[nn] = int(ret)
        return self.states

    #==========================================================================
    # set's
    #
    def set_volt(self, channel, volt) -> None:
        self.write_cmd(f"INST OUT{channel}\nVOLT {volt:3.3f}")

    def set_curr(self, channel,curr) -> None:
        self.write_cmd(f"INST OUT{channel}\nCURR {curr:3.3f}")

    def set_state(self, channel, state) -> None:
        self.write_cmd(f"INST OUT{channel}\nOUTP:STATE {state}")

    def set_states(self, states=[1,1,1,1]) -> None:
        for ch in [1,2,3,4]:
            self.write_cmd(f"INST OUT{ch}\nOUTP:STATE {states[ch-1]}")

    def set_volt_curr(self, channel, volt, curr) -> None:
        # APPL 6,2
        # APPL?
        self.write_cmd(f"INST OUT{channel}\nAPPL {volt},{curr}")

    #==========================================================================
    # get set velues
    ##
    def get_volt(self, channel) -> str:
        return self.send_cmd(f"INST OUT{channel}\nVOLT?")

    ##
    def get_curr(self, channel) -> str:
        return self.send_cmd(f"INST OUT{channel}\nCURR?")
    
    ##
    def get_state(self, channel) -> int:
        return int( self.send_cmd(f"INST OUT{channel}\nOUTP:STATE?") )

    #==========================================================================
    # measurements
    #
    def meas_all(self, chs=[1,2,3,4]) -> list:
        for ch in chs:
            self.values[2*(ch-1)  ] = str(self.meas_volt(ch) )
            self.values[2*(ch-1)+1] = str(self.meas_curr(ch) )
        return self.values

    def meas_volt(self, channel=[1,2,3,4]) -> str:
        return self.send_cmd(f"INST OUT{channel}\nMEAS:VOLT?")

    def meas_curr(self, channel=[1,2,3,4]) -> str:
        return self.send_cmd(f"INST OUT{channel}\nMEAS:CURR?")
    
    def measure_ldo(self) -> dict:
        self.hmp_dict['C1V'] = float(self.send_cmd(f"INST OUT1\nMEAS:VOLT?"))
        self.hmp_dict['C1A'] = float(self.send_cmd(f"INST OUT1\nMEAS:CURR?"))

        self.hmp_dict['C2V'] = float(self.send_cmd(f"INST OUT2\nMEAS:VOLT?"))
        self.hmp_dict['C2A'] = float(self.send_cmd(f"INST OUT2\nMEAS:CURR?"))
        
        return self.hmp_dict

    #==========================================================================
    def RunCommand(self):
        '''continous loop to check connection and send a command ...'''
        if self.serial_connection.closed:
            self.connect()
            logger.error('USB connection was lost')

        if self.Wcmnd != '':
            self.write_cmd( self.Wcmnd )
            # logger.debug( self.Wcmnd )
            self.Wcmnd = ''

        # elif self.Rcmnd != '':
        #     self.send_cmd( self.Rcmnd )
        #     self.Rcmnd != ''


###############################################################################
###############################################################################
if __name__ == '__main__':
    ''' '''
    try:
        hmp = Hmp4040(f"../ST3_BASE/config/mopo/MoPo_HMP4040.yaml")
        # hmp = Hmp4040(f"{os.getenv('HOME')}/ST3_BASE/config/ldo/LDO_HMP4040.yaml")
    except Exception as e:
        print(e)
        sys.exit(1)

    print( hmp.identify() )
    hmp.hmp_beep()
    print( hmp.ch_states() )

    hmp.gen_on()
    # hmp.ch_on([1, 2])
    # hmp.ch_off([2])

    print( hmp.meas_all())
    print( hmp.ch_states() )
    print( f'state {hmp.get_state(1)}' )

    import time
    for _ in range(30):
        time.sleep(0.1)

        print( hmp.ch_states([1, 2, 3, 4]) )
        # for ch in [1,2,3,4]:
        #     print( f'ch{ch}__state_{hmp.get_state(ch)}' )

    hmp.gen_off()

    # hmp.all_off()
