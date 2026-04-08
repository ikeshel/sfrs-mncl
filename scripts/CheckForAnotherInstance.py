#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

import sys, os

from PyQt5 import QtWidgets

#==========================================================================
def CheckForAnotherInstance(app_name, gui_warning=True):

    ''' check if other process with the same name is running'''
    error_msg=None
    # if os.popen('ps u').read().count(sys.argv[0]) > 1 :
    if os.popen('ps aux | grep %s' % app_name).read().count(app_name) > 3 :
        error_msg='It seems there is another \n'+app_name+'\n instance running!'
        if gui_warning == True:
            QtWidgets.QMessageBox.critical(None, 'ERROR', error_msg)
        else:
            print( error_msg )

    return error_msg
    
###############################################################################
# M A I N
###############################################################################
if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv) # create the application instance needed for the message box

    app_name = sys.argv[1] if len(sys.argv)>1 else sys.argv[0]
    print( 'app_name:', app_name )
    error_msg=CheckForAnotherInstance( app_name )
    print( error_msg )

    # app.exec_()
    # sys.exit(app.exec_())

