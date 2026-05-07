.PHONY: test coverage deploy clean

# Run all tests
test:
	python3 -m pytest tests/ -v

# Run tests with coverage report
coverage:
	python3 -m pytest tests/ --cov=dryrun_core --cov-report=term-missing --cov-report=html --cov-fail-under=100

# Deploy source to runtime location (tools/bin/)
deploy:
	cp dryrun_core.py ../bin/dryrun_core.py
	@echo "Deployed: tools/dryrun_core/dryrun_core.py -> tools/bin/dryrun_core.py"

# Clean test artifacts
clean:
	rm -rf .pytest_cache htmlcov .coverage
