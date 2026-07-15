PYTHON ?= python3
NPM ?= npm

.PHONY: help icons web test lint build validate bridge-src bridge-run all clean

help:
	@echo "VEQRA FORM - Build-Ziele:"
	@echo "  make icons      - Icons erzeugen"
	@echo "  make web        - Weboberfläche bauen (web/dist)"
	@echo "  make test       - Tests ausfuehren (ohne Allplan)"
	@echo "  make lint       - Lint-Pruefung (ruff)"
	@echo "  make build      - dist/VeqraForm.allep bauen (inkl. Tests)"
	@echo "  make validate   - ALLEP-Paket validieren"
	@echo "  make bridge-src - dist/veqra-bridge-source.zip bauen"
	@echo "  make bridge-run - Bridge lokal starten (Testmodus)"
	@echo "  make all        - Icons, Web, Tests, Lint, Builds, Validierung"
	@echo "  make clean      - Build-Artefakte entfernen"

icons:
	$(PYTHON) tools/generate_icons.py

web:
	cd web && $(NPM) install --no-audit --no-fund && $(NPM) run build

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check PythonPartsScripts tests tools bridge

build: test lint
	$(PYTHON) tools/build_allep.py

validate:
	$(PYTHON) tools/validate_allep.py

bridge-src:
	$(PYTHON) tools/build_bridge_source.py

bridge-run:
	cd bridge && ../$(PYTHON) run_bridge.py

all: icons web test lint build validate bridge-src
	@echo ""
	@echo "Fertige Pakete:"
	@ls -lh dist/VeqraForm.allep dist/veqra-bridge-source.zip
	@ls -d web/dist

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" -not -path "./_external/*" -not -path "./_legacy/*" -not -path "./web/node_modules/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache dist/VeqraForm.allep dist/veqra-bridge-source.zip web/dist
	@echo "Build-Artefakte entfernt"
