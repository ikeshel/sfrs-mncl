
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "1.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import requests

from loguru import logger

from yaml_manager import YamlManager

###############################################################################
###############################################################################
class NetworkSession:
    '''    '''

    api_session = requests.Session()

    # Define the JSON data to send in the request body
    data = {"key": "value"}
    
    #==========================================================================
    def __init__(self, yaml='config/session.yaml'):

        self.SessionYaml = YamlManager(yaml)

        self.username = self.SessionYaml.get_key_or_set('USER', 'gsi')
        self.password = self.SessionYaml.get_key_or_set('PASS', 'pass')
        
        self.api_session.auth = (self.username, self.password)

        self.base_url = 'http://web-docs.gsi.de/~dtl-sts/api/'

    #==========================================================================
    def __del__(self):
        print('Destructor called, Network session closed.')

    #==========================================================================
    def get_api_id_reburn(self, name):
        ''' '''
        logger.debug(f'get_api_id_reburn {name}')

        # Set up the API endpoint URL
        # http://web-docs.gsi.de/~dtl-sts/api/read_smx_id.php?reburn_name=XA-000-08-002-003-007-021-00
        url = f"{self.base_url}read_smx_id.php?reburn_name={name}"
        logger.debug(url)
        
        # Make the API request
        response = self.api_session.get(url)

        # Check the response status code
        if response.status_code == 200:
            # Handle the successful response data
            # data = response.json()
            # print(data)
            data = response.json()
            logger.debug(data)

            # print( type(response) )

            logger.debug(data[0].get("id"))
            logger.debug(data[0].get("get_str"))

            return data[0]
        else:
            # Handle the error response
            logger.debug("Error: {}".format(response.text))

    #==========================================================================
    def get_api_id_for_str(self, name):
        ''' '''
        logger.debug(f'get_api_id_for_str {name}')

        # Set up the API endpoint URL
        # http://web-docs.gsi.de/~dtl-sts/api/read_smx_id.php?name=%27XA-000-09-004-001-002-019-08%27
        url = f"{self.base_url}read_smx_id.php?smx_id_by_wxy={name}"
        logger.debug(url)
        
        # Make the API request
        response = self.api_session.get(url)

        # Check the response status code
        if response.status_code == 200:
            # Handle the successful response data
            # data = response.json()
            # print(data)
            data = response.json()
            logger.debug(data)

            # print( type(response) )

            logger.debug(data[0].get("id"))
            logger.debug(data[0].get("get_str"))

            return int(data[0].get("id"))
        else:
            # Handle the error response
            logger.debug("Error: {}".format(response.text))

    #==========================================================================
    def get_api_id(self, ser=8):
        ''' '''
        batch = self.SessionYaml.val['BATCH'] # GSI-2, KIT-3, Wafer-4

        logger.debug('Last ID')

        # Set up the API endpoint URL
        url = f"{self.base_url}read_smx_id.php?ser={ser}&batch={batch}"
        logger.debug(url)

        # Make the API request
        response = self.api_session.get(url)

        # Check the response status code
        if response.status_code == 200:
            # Handle the successful response data
            # data = response.json()
            # print(data)
            data = response.json()
            logger.debug(data)

            # print( type(response) )

            logger.debug(data[0].get("id"))
            logger.debug(data[0].get("get_str"))

            return int(data[0].get("id"))
        else:
            # Handle the error response
            logger.debug("Error: {}".format(response.text))

    #==========================================================================
    def burned_api_id(self, smx_id, burned):
        ''' '''

        logger.debug('Last ID')

        # Set up the API endpoint URL
        url = f"{self.base_url}update_smx_id.php?smx_id={smx_id}&burned={burned}"
        logger.debug(url)

        # Make the API request
        response = self.api_session.get(url)
        # print( response )


    #==========================================================================
    def fill_pol2_calibration(self, data):
        ''' '''
        # http://web-docs.gsi.de/~dtl-sts/api/fill_calibration.php?calibration=
        # {'name':'ADC','asic_id':'XA-000-08-004-100-010-010-00', 'chi2':'1.0',  'ndf':'33',   'p0':'0.1', 'p0err':'0.2', 'p1':'1.1', 'p1err':'1.2', 'p2':'2.1', 'p2err':'2.2'}

        # Set up the API endpoint URL
        url = f"{self.base_url}fill_calibration.php?calibration="+str(data)
        logger.debug(url)

        # Make the API request
        response = self.api_session.get(url)
        logger.debug( response )

    #==========================================================================
    def insert_update_feb8_asics(self, feb_dict):
        ''' 
        http://web-docs.gsi.de/~dtl-sts/api/insert_update_feb8_asics.php?feb8={%27feb_sn%27:%20%271000%27,%20%27a0%27:%20%27XA-000-11-222-111-000-111-00%27,%20%27a1%27:%20%27XA-000-11-222-111-000-111-01%27,%20%27a2%27:%20%27XA-000-11-222-111-000-111-02%27,%20%27a3%27:%20%27XA-000-11-222-111-000-111-03%27,%20%27a4%27:%20%27XA-000-11-222-111-000-111-04%27,%20%27a5%27:%20%27XA-000-11-222-111-000-111-05%27,%20%27a6%27:%20%27XA-000-11-222-111-000-111-06%27,%20%27a7%27:%20%27XA-000-11-222-111-000-111-07%27,%20%27date_time%27:%20%272024-11-11%2011:11:11%27,%20%27comment%27:%20%27test%20feb8%20insertion%27}
        '''
        # Set up the API endpoint URL
        url = f"{self.base_url}insert_update_feb8_asics.php?feb8="+str(feb_dict)
        logger.debug(url)

        # Make the API request
        response = self.api_session.get(url)
        logger.debug( response )

    #==========================================================================
    def update_module_feb(self, module_name, feb_type, feb_sn):
        ''' 
        https://web-docs.gsi.de/~dtl-sts/api/update_module_feb.php?module_name=M0DR3T4000104B2&feb_a=1000

        https://web-docs.gsi.de/~dtl-sts/api/update_module_feb.php?module_name=M0DR3T4000104B2&feb_b=2000
        '''

        # Set up the API endpoint URL
        url = f"{self.base_url}update_module_feb.php?module_name={module_name}&feb_{feb_type}={feb_sn}"
        logger.debug(url)

        # Make the API request
        response = self.api_session.get(url)
        logger.debug( response )

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == '__main__':
    logger.debug('__main__')

    myses = NetworkSession('/home/irakli/ST3_BASE/config/session.yaml')

    myses.update_module_feb("M0DR3T4000104B2", "a", "2000")


    # feb_dict = {
    #     'feb_sn':'1000',
    #     'a0':'XA-000-11-222-111-000-113-00',
    #     'a1':'XA-000-11-222-111-000-113-01',
    #     'a2':'XA-000-11-222-111-000-113-02',
    #     'a3':'XA-000-11-222-111-000-113-03',
    #     'a4':'XA-000-11-222-111-000-113-04',
    #     'a5':'XA-000-11-222-111-000-113-05',
    #     'a6':'XA-000-11-222-111-000-113-06',
    #     'a7':'XA-000-11-222-111-000-113-07',
    #     'date_time':'2024-11-11 11:11:11', 
    #     'comment':'test feb8 insertion'
    # }
    # myses.insert_update_feb8_asics(feb_dict)
    
    # smx_id = myses.get_api_id(8)
    # print( smx_id )
    # myses.burned_api_id(smx_id, 1)
