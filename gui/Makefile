# 
# i.keshelashvili@gsi.de
# 
CC = pyuic5

SRCS = $(shell ls gui_*.ui)

MODULES = $(echo .ui=.py)

all: compiling ${MODULES}
	@echo 'done!'


mylist:
	@echo ${SRCS}
	@echo ${MODULES}

compiling:
	@echo 'compiling ui files...'
	@echo '---------------------'

	## COMMON
	${CC} gui_ModuleScanner.ui      -o gui_ModuleScanner.py                   
	${CC} gui_comments.ui    -o gui_comments.py                    
	${CC} gui_status.ui      -o gui_status.py                    
	${CC} gui_ucable.ui      -o gui_ucable.py                    
	${CC} gui_save.ui        -o gui_save.py                    

	## HMP4040
	${CC} gui_hmp.ui         -o gui_hmp.py                    
	${CC} gui_hmp_window.ui  -o gui_hmp_window.py                   

	## FEB8
	${CC} gui_feb8.ui             -o gui_feb8.py                    
	${CC} gui_feb8_hmp_server.ui  -o gui_feb8_hmp_server.py
	${CC} gui_feb8_emu_server.ui  -o gui_feb8_emu_server.py
	${CC} gui_feb8_temp_server.ui -o gui_feb8_temp_server.py                   

	${CC} gui_smx.ui              -o gui_smx.py

	## ASIC
	# ${CC} gui_EMUserver.ui          -o gui_EMUserver.py                   
	$(CC) gui_asic_emu_server.ui   -o gui_asic_emu_server.py
	${CC} gui_asic_temp_server.ui  -o gui_asic_temp_server.py                   
	${CC} gui_asic_test.ui   -o gui_asic_test.py                    


	## LDO
	${CC} gui_ldo_test.ui    -o gui_ldo_test.py                    

	## Module Powering gui_ldo_test
	${CC} gui_mopo_test.ui -o gui_mopo_test.py

	${CC} gui_hmp_EMU.ui     -o gui_hmp_EMU.py                    
	${CC} gui_hmp_Module.ui  -o gui_hmp_Module.py                    
	${CC} gui_hmp_LDO.ui     -o gui_hmp_LDO.py                    
	${CC} GUI_EMU_CONTROL.ui -o GUI_EMU_CONTROL.py                    
	${CC} GUI_HMP_CHANNEL.ui -o GUI_HMP_CHANNEL.py                    
	@echo '---------------------'

clean:
	rm -rv __pycache__
