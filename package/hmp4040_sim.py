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
# from usb_manager   import UsbManager
import random

###############################################################################
###############################################################################
class Hmp4040_Sim():
    '''    
    '''

    Rcmnd = '' # read command container
    Wcmnd = '' # write command container
    Wrtrn = '' # return container

    hmp_dict= {'C1V': 0.0, 'C1A': 0.0, 'C2V': 0.0, 'C2A': 0.0, 
               'C3V': 0.0, 'C3A': 0.0, 'C4V': 0.0, 'C4A': 0.0}

    test_data_0 = \
    [('2.387', '1.678', '1.788', '2.278', '2.384', '1.659', '1.797', '2.466', 1761356957.082863), 
     ('2.387', '1.522', '1.792', '2.394', '2.388', '1.659', '1.790', '2.482', 1761356957.585552), 
     ('2.387', '1.645', '1.795', '2.308', '2.386', '1.672', '1.795', '2.235', 1761356958.087038), 
     ('2.389', '1.424', '1.787', '2.297', '2.393', '1.506', '1.790', '2.444', 1761356958.593129), 
     ('2.389', '1.529', '1.790', '2.367', '2.397', '1.646', '1.794', '2.398', 1761356959.095253), 
     ('2.386', '1.510', '1.784', '2.423', '2.382', '1.425', '1.794', '2.238', 1761356959.596992), 
     ('2.393', '1.666', '1.790', '2.310', '2.383', '1.635', '1.786', '2.213', 1761356960.0992692), 
     ('2.387', '1.603', '1.788', '2.452', '2.385', '1.491', '1.781', '2.419', 1761356960.6018822), 
     ('2.383', '1.597', '1.782', '2.453', '2.397', '1.554', '1.799', '2.386', 1761356961.106307), 
     ('2.388', '1.461', '1.795', '2.263', '2.382', '1.523', '1.790', '2.476', 1761356961.611789), 
     ('2.391', '1.620', '1.782', '2.215', '2.399', '1.483', '1.798', '2.288', 1761356962.114062), 
     ('2.394', '1.569', '1.794', '2.457', '2.391', '1.545', '1.800', '2.387', 1761356962.6163259), 
     ('2.398', '1.500', '1.786', '2.335', '2.391', '1.680', '1.780', '2.451', 1761356963.118525), 
     ('2.391', '1.468', '1.791', '2.461', '2.383', '1.528', '1.786', '2.222', 1761356963.620169), 
     ('2.391', '1.597', '1.791', '2.331', '2.396', '1.546', '1.793', '2.405', 1761356964.1224499), 
     ('2.390', '1.678', '1.796', '2.371', '2.385', '1.475', '1.790', '2.267', 1761356964.624714), 
     ('2.395', '1.416', '1.788', '2.256', '2.392', '1.472', '1.789', '2.253', 1761356965.127063), 
     ('2.382', '1.683', '1.793', '2.361', '2.395', '1.513', '1.793', '2.391', 1761356965.62872), 
     ('2.382', '1.498', '1.789', '2.447', '2.386', '1.650', '1.795', '2.321', 1761356966.134392), 
     ('2.388', '1.576', '1.794', '2.491', '2.399', '1.409', '1.780', '2.390', 1761356966.638964), 
     ('2.393', '1.406', '1.799', '2.210', '2.389', '1.400', '1.783', '2.464', 1761356967.139704)]

    #==========================================================================
    def __init__(self, yaml=''):

        self.states   = [0,0,0,0]
        self.volts    = [0,0,0,0]
        self.currents = [0,0,0,0]
        self.values   = ['0','0','0','0', # V1,A1,V2,A2,V3,A3,V4,A4
                         '0','0','0','0']

        try:
            self.hmp_yaml = YamlManager( yaml ).mydict
            logger.debug(f'yaml file {self.hmp_yaml}')
        except:
            logger.error(f"No '{yaml}' file found")
            raise FileNotFoundError('No yaml file found')
            return

        # super().__init__(self.hmp_yaml['ID']) # call parent constructor

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
        return
        # logger.info( command )
        # logger.info('SYST:BEEP')

    #==========================================================================
    def __del__(self):
        print('Destructor called, USB connection closed.')
    
    #==========================================================================
    def identify(self):
        logger.info('*IDN?')

    #==========================================================================
    def hmp_beep(self):
        logger.info('SYST:BEEP')

    #==========================================================================
    def send_cmd(self, cmd):
        '''command with return'''
        # try:
        #     self.serial_connection.write(str.encode(cmd)+b"\r\n")
        #     return self.serial_connection.readline().decode().strip()
        # except:
        #     logger.error(serial.serialutil.SerialException)
        #     logger.error('USB connection was lost')
        #     return ''
        logger.info(f'{cmd}')

    #==========================================================================
    def write_cmd(self, cmd):
        '''command without return'''
        # if self.serial_connection.closed:
        #     self.connect()
        #     logger.error('USB connection was lost')
        # self.serial_connection.write(str.encode(cmd)+b"\r\n")
        logger.info(f'{cmd}')


    #==========================================================================
    def gen_on(self):
        self.states=[1,1,1,1]
        logger.info("OUTPUT:GENERAL ON")

    #==========================================================================
    def gen_off(self):
        self.states=[0,0,0,0]
        logger.info("OUTPUT:GENERAL OFF")

    #==========================================================================
    def all_off(self):
        logger.info(    "INST OUT1\nOUTP:STATE 0\n"\
                        "INST OUT2\nOUTP:STATE 0\n"\
                        "INST OUT3\nOUTP:STATE 0\n"\
                        "INST OUT4\nOUTP:STATE 0\n"\
                        "OUTPUT:GENERAL OFF")
        self.states=[1,1,1,1]

    #==========================================================================
    def all_on(self):
        logger.info(    "INST OUT1\nOUTP:STATE 1\n"\
                        "INST OUT2\nOUTP:STATE 1\n"\
                        "INST OUT3\nOUTP:STATE 1\n"\
                        "INST OUT4\nOUTP:STATE 1\n"\
                        "OUTPUT:GENERAL ON")
        self.states=[0,0,0,0]

    #==========================================================================
    def ch_on(self, chs=[1,2,3,4]) -> None:
        logger.debug(f"Turning ON channels: {chs}")
        for ch in chs:
            self.states[ch-1]=True
            logger.info(f'INST OUT{str(ch)}\nOUTP:STATE 1')
            # self.Wcmnd = f'INST OUT{str(ch)}\nOUTP:STATE 1'
            # self.RunCommand()

    #==========================================================================
    def ch_off(self, chs=[1,2,3,4]) -> None:
        logger.debug(f"Turning OFF channels: {chs}")
        for ch in chs:
            self.states[ch-1]=False
            logger.info(f'INST OUT{str(ch)}\nOUTP:STATE 0')
            # self.Wcmnd = f'INST OUT{str(ch)}\nOUTP:STATE 0'
            # self.RunCommand()

    #==========================================================================
    def ch_states(self, chs=[1,2,3,4]) -> list:
        # for ch in chs:
            # ret = self.send_cmd(f"INST OUT{int(ch)}\nOUTP:STATE?")
            # ret = self.states[ch-1]
            # nn = int(ch)-1
            # self.states[nn] = int(ret)
        return self.states

    #==========================================================================
    # set's
    #
    def set_volt(self, channel, volt) -> None:
        logger.info(f"INST OUT{channel}\nVOLT {volt:3.3f}")

    def set_curr(self, channel,curr) -> None:
        logger.info(f"INST OUT{channel}\nCURR {curr:3.3f}")

    def set_state(self, channel, state) -> None:
        logger.info(f"INST OUT{channel}\nOUTP:STATE {state}")
        self.states[channel-1] = state

    def set_states(self, states=[1,1,1,1]) -> None:
        for ch in [1,2,3,4]:
            logger.info(f"INST OUT{ch}\nOUTP:STATE {states[ch-1]}")
            self.states = states

    def set_volt_curr(self, channel, volt, curr) -> None:
        # APPL 6,2
        # APPL?
        logger.info(f"INST OUT{channel}\nAPPL {volt},{curr}")

    #==========================================================================
    # get set velues
    ##
    def get_volt(self, channel) -> str:
        # return self.send_cmd(f"INST OUT{channel}\nVOLT?")
        return str(self.hmp_yaml[f'V{channel}'])

    ##
    def get_curr(self, channel) -> str:
        # return self.send_cmd(f"INST OUT{channel}\nCURR?")
        return str(self.hmp_yaml[f'A{channel}'])

    ##
    def get_state(self, channel) -> int:
        # return int( self.send_cmd(f"INST OUT{channel}\nOUTP:STATE?") )
        return int(random.random())


    #==========================================================================
    # measurements
    #
    def meas_all(self, chs=[1,2,3,4]) -> list:
        for ch in chs:
            self.values[2*(ch-1)  ] = str(self.meas_volt(ch) )
            self.values[2*(ch-1)+1] = str(self.meas_curr(ch) )
        return self.values

    def meas_volt(self, channel=[1,2,3,4]) -> str:
        # return self.send_cmd(f"INST OUT{channel}\nMEAS:VOLT?")
        if self.states[channel-1]:
            setval = float(self.hmp_yaml[f'V{channel}'])
            return f'{setval -0.02*random.random():4.3f}'
        else:
            return '0.0'
       
    def meas_curr(self, channel=[1,2,3,4]) -> str:
        # return self.send_cmd(f"INST OUT{channel}\nMEAS:CURR?")
        if self.states[channel-1]:
            setval = float(self.hmp_yaml[f'A{channel}'])
            return f'{setval -0.5 -0.3*random.random():4.3f}'
        else:
            return '0.0'
    
    def measure_ldo(self) -> dict:
        self.hmp_dict['C1V'] = float(2.2+0.2*random.random())
        self.hmp_dict['C1A'] = float(2.0+0.2*random.random())

        self.hmp_dict['C2V'] = float(2.2+0.2*random.random())
        self.hmp_dict['C2A'] = float(2.0+0.2*random.random())
        
        return self.hmp_dict

    #==========================================================================
    def RunCommand(self):
        '''continous loop to check connection and send a command ...'''
        if self.serial_connection.closed:
            self.connect()
            logger.error('USB connection was lost')

        if self.Wcmnd != '':
            logger.info( self.Wcmnd )
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
        hmp = Hmp4040_Sim(f"../ST3_BASE/config/mopo/MoPo_HMP4040.yaml")
        # hmp = Hmp4040(f"{os.getenv('HOME')}/ST3_BASE/config/ldo/LDO_HMP4040.yaml")
    except Exception as e:
        print(e)
        sys.exit(1)

    # print( hmp.identify() )
    # hmp.hmp_beep()
    print( hmp.ch_states() )

    hmp.gen_on()
    # hmp.ch_on([1, 2])
    # hmp.ch_off([2])

    print( hmp.meas_all())
    print( hmp.ch_states() )
    print( f'state {hmp.get_state(1)}' )

    import time
    for _ in range(10):
        time.sleep(0.1)

        print( hmp.ch_states([1, 2, 3, 4]) )
        # for ch in [1,2,3,4]:
        #     print( f'ch{ch}__state_{hmp.get_state(ch)}' )

    hmp.gen_off()

    # hmp.all_off()
