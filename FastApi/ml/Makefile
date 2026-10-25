.PHONY: data validate eval-baseline test pdf-corpus pdf-eval pdf-gates
UV ?= uv run --python 3.13 --group ml-core
data:
	$(UV) python -m ml.training.common.build_data
validate:
	$(UV) python -m ml.evaluation.validate
eval-baseline:
	$(UV) python -m ml.training.intent.baseline
test:
	$(UV) pytest ml/tests -q --no-cov

PDF_UV ?= uv run --python 3.13 --group pdf-corpus --group ml-core
# Build the golden PDFs into ml/pdf_golden/.build/ (never committed) and verify the frozen ground truth.
pdf-corpus:
	$(PDF_UV) python -m ml.pdf_golden.build_corpus
# Build the corpus, run the pipeline under test (default: NotImplementedPipeline, all metrics null) and write metrics per slice.
pdf-eval: pdf-corpus
	$(PDF_UV) python -m ml.pdf_golden.run_pdf_eval $(if $(PIPELINE),--pipeline $(PIPELINE),)
# RED on purpose until each stage lands.
pdf-gates:
	$(PDF_UV) pytest ml/pdf_golden/tests/test_pdf_gates.py -m gates -q --no-cov
