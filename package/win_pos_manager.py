
__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2021, The CBM-STS Project"
__version__    = "3.0.0"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import yaml
from loguru import logger

class WindowPositionManager:
    def __init__(self):

        self.yaml_filename = f".size_pos_{self.__class__.__name__}.yaml"

        self.xx = 10
        self.yy = 10
        self.ww = 1000
        self.hh = 800

    #==========================================================================
    def read_window_data(self):
        
        try:
            with open(self.yaml_filename, "r") as yaml_file:
                window_data = yaml.safe_load(yaml_file)

            self.xx = window_data.get("x_position", self.xx)
            self.yy = window_data.get("y_position", self.yy)
            self.ww = window_data.get("width", self.ww)
            self.hh = window_data.get("height", self.hh)

            logger.debug(f"Window size and position loaded from {self.yaml_filename}")
            logger.debug(window_data)
            return True

        except FileNotFoundError:
            logger.debug(f"No saved window data found in {self.yaml_filename}")
            return False

    #==========================================================================
    def save_window_data(self):

        window_data = {
            "x_position": self.pos().x(),
            "y_position": self.pos().y(),
            "width": self.size().width(),
            "height": self.size().height()
        }

        with open(self.yaml_filename, "w") as yaml_file:
            yaml.dump(window_data, yaml_file)

        logger.debug(f"Window size and position saved to {self.yaml_filename}")

#******************************************************************************
# M A I N
#******************************************************************************
if __name__ == '__main__':

    win = WindowPositionManager()
    win.yaml_filename = ".size_pos_MoPoTest.yaml"
    logger.debug(win.read_window_data())
    logger.debug(f"x: {win.xx}, y: {win.yy}, w: {win.ww}, h: {win.hh}")