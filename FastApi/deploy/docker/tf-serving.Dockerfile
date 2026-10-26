# Serves the exported intent SavedModels (ml/artifacts/intent/<version>) over REST on :8501.
FROM tensorflow/serving:2.18.0
COPY ml/artifacts/intent /models/intent
COPY deploy/docker/tf-serving/models.config /models/models.config
EXPOSE 8501
ENTRYPOINT ["/usr/bin/tf_serving_entrypoint.sh"]
CMD ["--model_config_file=/models/models.config", "--model_config_file_poll_wait_seconds=0", "--rest_api_port=8501"]
