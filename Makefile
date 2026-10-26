PYTHON = python3
MAIN = main.py
MAP ?= maps/easy/01_linear_path.txt
ARGS ?=

MYPY_FLAGS = --warn-return-any \
             --warn-unused-ignores \
             --ignore-missing-imports \
             --disallow-untyped-defs \
             --check-untyped-defs

.PHONY: install run visual debug clean lint lint-strict run_all

install:
	pip install -r requirements.txt

run:
	$(PYTHON) $(MAIN) $(MAP) $(ARGS)

visual:
	$(PYTHON) $(MAIN) $(MAP) --visual

debug:
	$(PYTHON) -m pdb $(MAIN) $(MAP) $(ARGS)

# run maps
run_easy-%:
	$(PYTHON) $(MAIN) maps/easy/$*_*.txt $(ARGS)

run_medium-%:
	$(PYTHON) $(MAIN) maps/medium/$*_*.txt $(ARGS)

run_hard-%:
	$(PYTHON) $(MAIN) maps/hard/$*_*.txt $(ARGS)

run_challenger-%:
	$(PYTHON) $(MAIN) maps/challenger/$*_*.txt $(ARGS)
# run maps with visuals 
visual_easy-%:
	$(PYTHON) $(MAIN) maps/easy/$*_*.txt --visual

visual_medium-%:
	$(PYTHON) $(MAIN) maps/medium/$*_*.txt --visual

visual_hard-%:
	$(PYTHON) $(MAIN) maps/hard/$*_*.txt --visual

visual_challenger-%:
	$(PYTHON) $(MAIN) maps/challenger/$*_*.txt --visual

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	flake8 .  --exclude=.venv
	mypy . --exclude=.venv $(MYPY_FLAGS)

lint-strict:
	flake8 . --exclude=.venv
	mypy . --exclude .venv --strict