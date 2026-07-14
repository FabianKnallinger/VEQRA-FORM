PYTHON ?= python3

.PHONY: help icons test lint build validate all clean

help:
	@echo "VEQRA FORM - Build-Ziele:"
	@echo "  make icons     - Icons erzeugen"
	@echo "  make test      - Tests ausfuehren (ohne Allplan)"
	@echo "  make lint      - Lint-Pruefung (ruff)"
	@echo "  make build     - dist/VeqraForm.allep bauen (inkl. Tests)"
	@echo "  make validate  - ALLEP-Paket validieren"
	@echo "  make all       - Icons, Tests, Lint, Build, Validierung"
	@echo "  make clean     - Build-Artefakte entfernen"

icons:
	$(PYTHON) tools/generate_icons.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check PythonPartsScripts tests tools

build: test lint
	$(PYTHON) tools/build_allep.py

validate:
	$(PYTHON) tools/validate_allep.py

all: icons test lint build validate
	@echo ""
	@echo "Fertiges Paket:"
	@ls -lh dist/VeqraForm.allep

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" -not -path "./_external/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache dist/VeqraForm.allep
	@echo "Build-Artefakte entfernt"
