#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__license__    = ""
__version__    = "1.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

"""YAML file manager"""

import yaml

from loguru import logger 

###############################################################################
###############################################################################
class YamlManager(): # manager for yaml files

    #==========================================================================
    def __init__(self, inFile):

        self.yaml_file_name = inFile

        self.read_yaml()
    
    #==========================================================================
    def read_yaml(self):        
        try:
            with open(self.yaml_file_name, 'r') as fin:
                logger.debug( f'Config file {self.yaml_file_name} found!')
                self.mydict = yaml.load(fin, Loader=yaml.FullLoader)
        except:
            logger.error( f"Config file {self.yaml_file_name} is not found!!!")
            raise FileNotFoundError(f"Config file {self.yaml_file_name} is not found!!!")

    #==========================================================================
    def save_yaml(self):
       ''' if the status of the buttons are changed, new yaml is saved '''
       try:
            with open(self.yaml_file_name, 'w') as fout:
                yaml.dump(self.mydict, fout, sort_keys=False, allow_unicode=True)
                logger.debug(f'New config {self.yaml_file_name} file saved')
       except:
            logger.error(f"Can't write {self.yaml_file_name} yaml file!!!")
            # raise FileNotFoundError(f"Can't write {self.yaml_file_name} yaml file!!!")
       
    #==========================================================================
    def get_dict(self):
        ''' return dictionary from yaml file '''
        return self.mydict
    
    #==========================================================================
    def get_key_or_set(self, key, default):
        ''' get value from yaml file or return default value '''
        try:
            return self.mydict[key]
        except:
            logger.warning(f'Key {key} not found in {self.yaml_file_name} file')
            logger.warning(f'Default value {default} will be set')
            return default

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == '__main__':
    yaml_manager = YamlManager("config.yaml")
    mydict = yaml_manager.get_dict()
    logger.debug(mydict)