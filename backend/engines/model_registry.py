"""
Model Registry - Version Control and Management for ML Models
"""

import hashlib
import json
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a registered model"""

    version: str
    created_at: str
    model_type: str
    accuracy: float
    drift_score: float
    training_samples: int
    validation_samples: int
    hyperparameters: Dict[str, Any]
    feature_names: List[str]
    checksum: str
    promoted: bool = False
    champion: bool = False
    notes: str = ""


class ModelRegistry:
    """
    Model Registry for version control, tracking, and rollback.

    Features:
    - Model versioning
    - Metadata tracking
    - Checksum verification
    - Rollback capabilities
    - Audit logging
    """

    def __init__(self, registry_dir: str = "models"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.registry_dir / "registry.json"
        self.models: Dict[str, ModelMetadata] = {}

        # Load existing registry
        self._load_registry()

        logger.info(f"Model Registry initialized at {self.registry_dir}")

    def register_model(self, model: Any, metadata: ModelMetadata) -> str:
        """
        Register a new model with metadata.

        Parameters:
        -----------
        model : Any
            The trained model object
        metadata : ModelMetadata
            Model metadata

        Returns:
        --------
        str
            Version ID of registered model
        """
        version = metadata.version
        model_path = self.registry_dir / f"model_{version}.pkl"

        # Save model
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        # Calculate checksum
        checksum = self._calculate_checksum(model_path)
        metadata.checksum = checksum

        # Store metadata
        self.models[version] = metadata
        self._save_registry()

        logger.info(
            f"Model registered: version={version}, accuracy={metadata.accuracy:.4f}"
        )

        # Audit log
        self._log_audit("register", version, metadata)

        return version

    def load_model(self, version: Optional[str] = None) -> Optional[Any]:
        """
        Load a model by version. If no version specified, loads latest champion.

        Parameters:
        -----------
        version : str, optional
            Model version to load. If None, loads latest champion.

        Returns:
        --------
        Any
            Loaded model object, or None if not found
        """
        if version is None:
            # Get latest champion
            metadata = self.get_champion_model()
            if metadata is None:
                logger.warning("No champion model found")
                return None
            version = metadata.version

        model_path = self.registry_dir / f"model_{version}.pkl"

        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return None

        # Verify checksum
        if version in self.models:
            stored_checksum = self.models[version].checksum
            current_checksum = self._calculate_checksum(model_path)

            if stored_checksum != current_checksum:
                logger.error(
                    f"Checksum mismatch for model {version}! File may be corrupted."
                )
                return None

        # Load model
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        logger.info(f"Model loaded: version={version}")
        return model

    def promote_model(self, version: str) -> bool:
        """
        Promote a model version (mark as promoted).

        Parameters:
        -----------
        version : str
            Model version to promote

        Returns:
        --------
        bool
            True if successful
        """
        if version not in self.models:
            logger.error(f"Model version {version} not found")
            return False

        self.models[version].promoted = True
        self._save_registry()

        logger.info(f"Model promoted: version={version}")
        self._log_audit("promote", version, self.models[version])

        return True

    def set_champion(self, version: str) -> bool:
        """
        Set a model as the champion (currently deployed).

        Parameters:
        -----------
        version : str
            Model version to set as champion

        Returns:
        --------
        bool
            True if successful
        """
        if version not in self.models:
            logger.error(f"Model version {version} not found")
            return False

        # Remove champion flag from all models
        for v in self.models:
            self.models[v].champion = False

        # Set new champion
        self.models[version].champion = True
        self._save_registry()

        logger.info(f"Champion model set: version={version}")
        self._log_audit("set_champion", version, self.models[version])

        return True

    def get_champion_model(self) -> Optional[ModelMetadata]:
        """Get metadata of current champion model"""
        for version, metadata in self.models.items():
            if metadata.champion:
                return metadata

        # If no champion, return latest
        return self.get_latest_model()

    def get_latest_model(self) -> Optional[ModelMetadata]:
        """Get metadata of latest registered model"""
        if not self.models:
            return None

        # Sort by created_at
        sorted_models = sorted(
            self.models.items(), key=lambda x: x[1].created_at, reverse=True
        )

        return sorted_models[0][1]

    def get_model_metadata(self, version: str) -> Optional[ModelMetadata]:
        """Get metadata for a specific version"""
        return self.models.get(version)

    def list_models(self) -> List[ModelMetadata]:
        """List all registered models"""
        return list(self.models.values())

    def rollback_to_version(self, version: str) -> bool:
        """
        Rollback to a previous model version by setting it as champion.

        Parameters:
        -----------
        version : str
            Version to rollback to

        Returns:
        --------
        bool
            True if successful
        """
        if version not in self.models:
            logger.error(f"Cannot rollback: version {version} not found")
            return False

        success = self.set_champion(version)

        if success:
            logger.warning(f"⚠️ ROLLBACK executed to version {version}")
            self._log_audit("rollback", version, self.models[version])

        return success

    def delete_model(self, version: str) -> bool:
        """
        Delete a model version (cannot delete champion).

        Parameters:
        -----------
        version : str
            Version to delete

        Returns:
        --------
        bool
            True if successful
        """
        if version not in self.models:
            return False

        if self.models[version].champion:
            logger.error("Cannot delete champion model")
            return False

        # Delete model file
        model_path = self.registry_dir / f"model_{version}.pkl"
        if model_path.exists():
            model_path.unlink()

        # Remove from registry
        del self.models[version]
        self._save_registry()

        logger.info(f"Model deleted: version={version}")
        self._log_audit("delete", version, None)

        return True

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _load_registry(self):
        """Load registry from disk"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                data = json.load(f)
                self.models = {k: ModelMetadata(**v) for k, v in data.items()}
            logger.info(f"Loaded {len(self.models)} models from registry")

    def _save_registry(self):
        """Save registry to disk"""
        data = {k: asdict(v) for k, v in self.models.items()}
        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def _log_audit(self, action: str, version: str, metadata: Optional[ModelMetadata]):
        """Log audit trail"""
        audit_dir = Path("logs/audit")
        audit_dir.mkdir(parents=True, exist_ok=True)

        audit_file = audit_dir / "model_registry_audit.jsonl"

        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "version": version,
            "metadata": asdict(metadata) if metadata else None,
        }

        with open(audit_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
