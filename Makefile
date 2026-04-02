
all:
	@echo "Building the project..."
	@make -C gui/

clean:
	@echo "Cleaning the project..."
	@rm -rv */__pycache__
