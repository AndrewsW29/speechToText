.PHONY: data validate eval-baseline test
UV ?= uv run --python 3.13 --group ml-core
data:
	$(UV) python -m ml.training.common.build_data
validate:
	$(UV) python -m ml.evaluation.validate
eval-baseline:
	$(UV) python -m ml.training.intent.baseline
test:
	$(UV) pytest ml/tests -q --no-cov
