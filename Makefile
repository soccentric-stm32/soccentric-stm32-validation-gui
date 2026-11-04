PYTHON ?= python3
VENV ?= .venv

.PHONY: help install run cli lint protocol icons package clean

help:
	@echo "install   create a venv and install the project"
	@echo "run       start the GUI"
	@echo "cli       run the simulator CLI (ADC group)"
	@echo "lint      ruff check on the application sources"
	@echo "protocol  regenerate the Python HWLINK bindings (needs flatc)"
	@echo "icons     render the SVG app icon sources"
	@echo "package   build the package for the current OS"

install:
	$(PYTHON) -m venv --system-site-packages $(VENV)
	$(VENV)/bin/pip install -e ".[dev,packaging]"

run:
	$(VENV)/bin/hwval-studio

cli:
	$(VENV)/bin/hwval-studio --cli --simulate hwval --group ADC --no-report

lint:
	$(VENV)/bin/python -m ruff check src scripts --exclude src/hwval_studio/protocol/generated

protocol:
	$(VENV)/bin/python scripts/gen_protocol.py

icons:
	$(VENV)/bin/python scripts/make_icons.py

package:
	@if [ "$$(uname -s)" = "Darwin" ]; then packaging/build-macos.sh; \
	 elif [ "$$(uname -s)" = "Linux" ]; then packaging/build-linux.sh; \
	 else echo "On Windows run packaging\\build-windows.ps1"; exit 1; fi

clean:
	rm -rf build dist .ruff_cache .mypy_cache
