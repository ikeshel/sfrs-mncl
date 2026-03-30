
#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__version__    = "3.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import csv
from loguru import logger 

#################################################################################
#################################################################################
class CSVManager:
    '''CSV Manager class to handle CSV file operations.'''

    #==========================================================================
    def __init__(self, filename):
        self.filename = filename

    #==========================================================================
    def read_csv(self):
        with open(self.filename, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                print(row)

    #==========================================================================
    def write_csv(self, data):
        '''Write data to a CSV file.'''

        with open(self.filename, mode='w') as file:
            writer = csv.writer(file)
            writer.writerow(['smx','Time', 'Temperature'])
            writer.writerows(data)

        file.close()
        logger.debug(f"Data written to {self.filename}")
