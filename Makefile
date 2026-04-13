
all:
	@echo "Building the project..."
	@make -C gui/

install:
	@echo "Installing Desktop icons..."
# 	@cp -v gui/*.desktop ${HOME}/.local/share/applications/
	@cp -vf gui/*.desktop ${HOME}/Desktop/

clean:
	@echo "Cleaning the project..."
	@rm -rv */__pycache__
