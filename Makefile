.PHONY: all run clean

VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

run: $(VENV)/bin/activate
	$(PYTHON) bot.py

$(VENV)/bin/activate: requirements.txt
	python3.10 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

all: $(VENV)/bin/activate

clean:
	rm -rf __pycache__
	rm -rf $(VENV)
	find . -type f -name ‘*.pyc’ -delete