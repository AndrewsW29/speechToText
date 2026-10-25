"""Register a trained model: refused unless the run is fully reproducible."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED = ("git_sha", "image_digest", "dataset_hash", "seeds", "hyperparameters", "metrics")
CARD_TEMPLATE = Path(__file__).with_name("model_card.md")


class MissingMetadataError(ValueError):
    """The run lacks metadata needed to reproduce it; an unreproducible model is not registered."""


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    git_sha: str
    image_digest: str
    dataset_hash: str
    seeds: Mapping[str, int]
    hyperparameters: Mapping[str, Any]
    metrics: Mapping[str, Any]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ModelMetadata:
        missing = [k for k in REQUIRED if not data.get(k)]
        if missing:
            raise MissingMetadataError(f"cannot register: missing {', '.join(missing)}")
        return cls(**{k: data[k] for k in REQUIRED})


def render_model_card(
    meta: ModelMetadata, owner: str, known_failures: list[str] | None = None
) -> str:
    scalar = {k: v for k, v in meta.metrics.items() if isinstance(v, int | float)}
    slices = meta.metrics.get("slices", {})
    return CARD_TEMPLATE.read_text(encoding="utf-8").format(
        git_sha=meta.git_sha,
        image_digest=meta.image_digest,
        dataset_hash=meta.dataset_hash,
        owner=owner,
        metrics="\n".join(f"- {k}: {v:.3f}" for k, v in sorted(scalar.items())) or "- none",
        slices="\n".join(f"- {k}: {v:.3f}" for k, v in sorted(slices.items())) or "- none",
        failures="\n".join(f"- {f}" for f in (known_failures or ["not yet characterised"])),
        hyperparameters="\n".join(f"- {k}: {v}" for k, v in sorted(meta.hyperparameters.items())),
        seeds=", ".join(f"{k}={v}" for k, v in sorted(meta.seeds.items())),
    )


def register_model(
    metadata: Mapping[str, Any],
    artifact_dir: Path,
    tracking_uri: str,
    model_name: str = "intent",
    owner: str = "ml-team",
    alias: str = "challenger",
    artifact_root: Path | None = None,
) -> str:
    """Log the run and register an immutable version; returns the version number.

    `tracking_uri` should be a database URI (e.g. `sqlite:///.../mlflow.db`); MLflow's file store
    is in maintenance mode. Artifacts go under `artifact_root` (default: next to the database).
    """
    meta = ModelMetadata.from_dict(metadata)  # raises before touching MLflow
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    import mlflow
    from mlflow import MlflowClient

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_registry_uri(tracking_uri)
    root = artifact_root or Path(tracking_uri.removeprefix("sqlite:///")).parent / "artifacts"
    root.mkdir(parents=True, exist_ok=True)
    existing = MlflowClient(tracking_uri, tracking_uri).get_experiment_by_name(model_name)
    experiment_id = (
        existing.experiment_id
        if existing
        else mlflow.create_experiment(model_name, artifact_location=root.resolve().as_uri())
    )
    mlflow.set_experiment(experiment_id=experiment_id)
    card = artifact_dir / "MODEL_CARD.md"
    card.write_text(render_model_card(meta, owner), encoding="utf-8")
    with mlflow.start_run(run_name=f"{model_name}-{meta.git_sha[:7]}") as run:
        mlflow.log_params({f"hp.{k}": v for k, v in meta.hyperparameters.items()})
        mlflow.log_params({f"seed.{k}": v for k, v in meta.seeds.items()})
        mlflow.log_metrics(
            {k: float(v) for k, v in meta.metrics.items() if isinstance(v, int | float)}
        )
        mlflow.set_tags(
            {
                "git_sha": meta.git_sha,
                "image_digest": meta.image_digest,
                "dataset_hash": meta.dataset_hash,
            }
        )
        mlflow.log_artifacts(str(artifact_dir))
        client = MlflowClient(tracking_uri=tracking_uri, registry_uri=tracking_uri)
        try:
            client.create_registered_model(model_name)
        except mlflow.exceptions.MlflowException:
            pass  # already exists
        version = client.create_model_version(
            model_name,
            source=run.info.artifact_uri,
            run_id=run.info.run_id,
            tags={"git_sha": meta.git_sha, "dataset_hash": meta.dataset_hash},
        )
    client.set_registered_model_alias(model_name, alias, version.version)
    return str(version.version)
