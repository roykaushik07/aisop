"""
JSON-based repository for storing and retrieving SOPs.

This module provides CRUD operations, search functionality, and caching
for Standard Operating Procedures stored as JSON files.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from threading import Lock

from sop_models import SOP

logger = logging.getLogger(__name__)


class SOPRepository:
    """JSON file-based repository for SOPs with caching."""

    def __init__(
        self,
        storage_path: str = "./data/sops.json",
        cache_ttl_seconds: int = 300
    ):
        """
        Initialize SOP repository.

        Args:
            storage_path: Path to JSON file for storing SOPs
            cache_ttl_seconds: How long to cache SOPs in memory
        """
        self.storage_path = Path(storage_path)
        self.cache_ttl_seconds = cache_ttl_seconds

        # Thread-safe cache
        self._cache: Optional[List[SOP]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_lock = Lock()

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file if it doesn't exist
        if not self.storage_path.exists():
            self._write_to_disk([])

    def get_all(self, force_refresh: bool = False) -> List[SOP]:
        """
        Get all SOPs.

        Args:
            force_refresh: Force reload from disk, bypassing cache

        Returns:
            List of all SOPs
        """
        with self._cache_lock:
            # Check if cache is valid
            if (
                not force_refresh
                and self._cache is not None
                and self._cache_timestamp is not None
                and datetime.now() - self._cache_timestamp < timedelta(seconds=self.cache_ttl_seconds)
            ):
                logger.debug("Returning SOPs from cache")
                return self._cache.copy()

            # Load from disk
            logger.debug("Loading SOPs from disk")
            sops = self._load_from_disk()

            # Update cache
            self._cache = sops
            self._cache_timestamp = datetime.now()

            return sops.copy()

    def get_by_id(self, sop_id: str) -> Optional[SOP]:
        """
        Get a specific SOP by ID.

        Args:
            sop_id: SOP identifier

        Returns:
            SOP if found, None otherwise
        """
        sops = self.get_all()
        for sop in sops:
            if sop.sop_id == sop_id:
                return sop
        return None

    def search_by_keywords(self, keywords: List[str]) -> List[SOP]:
        """
        Search SOPs by trigger keywords.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of SOPs that match any of the keywords
        """
        sops = self.get_all()
        matching_sops = []

        keywords_lower = [kw.lower() for kw in keywords]

        for sop in sops:
            # Check if any trigger keyword matches
            for trigger_kw in sop.trigger_keywords:
                if any(kw in trigger_kw.lower() for kw in keywords_lower):
                    matching_sops.append(sop)
                    break

            # Also check in description
            if sop not in matching_sops:
                if any(kw in sop.description.lower() for kw in keywords_lower):
                    matching_sops.append(sop)

        return matching_sops

    def search_by_tags(self, tags: List[str]) -> List[SOP]:
        """
        Search SOPs by tags.

        Args:
            tags: List of tags to search for

        Returns:
            List of SOPs that have any of the tags
        """
        sops = self.get_all()
        matching_sops = []

        tags_lower = [tag.lower() for tag in tags]

        for sop in sops:
            sop_tags_lower = [tag.lower() for tag in sop.tags]
            if any(tag in sop_tags_lower for tag in tags_lower):
                matching_sops.append(sop)

        return matching_sops

    def create(self, sop: SOP) -> bool:
        """
        Create a new SOP.

        Args:
            sop: SOP to create

        Returns:
            True if successful, False if SOP ID already exists
        """
        with self._cache_lock:
            sops = self._load_from_disk()

            # Check if ID already exists
            if any(s.sop_id == sop.sop_id for s in sops):
                logger.warning(f"SOP with ID {sop.sop_id} already exists")
                return False

            sops.append(sop)
            self._write_to_disk(sops)

            # Invalidate cache
            self._cache = None
            self._cache_timestamp = None

            logger.info(f"Created SOP: {sop.sop_id}")
            return True

    def update(self, sop: SOP) -> bool:
        """
        Update an existing SOP.

        Args:
            sop: SOP with updated data

        Returns:
            True if successful, False if SOP not found
        """
        with self._cache_lock:
            sops = self._load_from_disk()

            # Find and replace
            for i, existing_sop in enumerate(sops):
                if existing_sop.sop_id == sop.sop_id:
                    sops[i] = sop
                    self._write_to_disk(sops)

                    # Invalidate cache
                    self._cache = None
                    self._cache_timestamp = None

                    logger.info(f"Updated SOP: {sop.sop_id}")
                    return True

            logger.warning(f"SOP {sop.sop_id} not found for update")
            return False

    def delete(self, sop_id: str) -> bool:
        """
        Delete an SOP.

        Args:
            sop_id: ID of SOP to delete

        Returns:
            True if successful, False if SOP not found
        """
        with self._cache_lock:
            sops = self._load_from_disk()

            # Filter out the SOP
            new_sops = [s for s in sops if s.sop_id != sop_id]

            if len(new_sops) == len(sops):
                logger.warning(f"SOP {sop_id} not found for deletion")
                return False

            self._write_to_disk(new_sops)

            # Invalidate cache
            self._cache = None
            self._cache_timestamp = None

            logger.info(f"Deleted SOP: {sop_id}")
            return True

    def export_to_file(self, export_path: str) -> bool:
        """
        Export all SOPs to a JSON file.

        Args:
            export_path: Path to export file

        Returns:
            True if successful
        """
        try:
            sops = self.get_all()
            export_path_obj = Path(export_path)
            export_path_obj.parent.mkdir(parents=True, exist_ok=True)

            with open(export_path_obj, 'w') as f:
                json.dump(
                    [sop.model_dump() for sop in sops],
                    f,
                    indent=2
                )

            logger.info(f"Exported {len(sops)} SOPs to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export SOPs: {e}")
            return False

    def import_from_file(
        self,
        import_path: str,
        overwrite_existing: bool = False
    ) -> int:
        """
        Import SOPs from a JSON file.

        Args:
            import_path: Path to import file
            overwrite_existing: If True, overwrite SOPs with same ID

        Returns:
            Number of SOPs imported
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)

            imported_count = 0

            for sop_data in data:
                sop = SOP(**sop_data)

                if overwrite_existing:
                    # Try update first, then create
                    if not self.update(sop):
                        if self.create(sop):
                            imported_count += 1
                    else:
                        imported_count += 1
                else:
                    # Only create if doesn't exist
                    if self.create(sop):
                        imported_count += 1

            logger.info(f"Imported {imported_count} SOPs from {import_path}")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import SOPs: {e}")
            return 0

    def clear_cache(self):
        """Clear the in-memory cache."""
        with self._cache_lock:
            self._cache = None
            self._cache_timestamp = None
            logger.debug("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get repository statistics.

        Returns:
            Dictionary with statistics
        """
        sops = self.get_all()

        tags_count = {}
        for sop in sops:
            for tag in sop.tags:
                tags_count[tag] = tags_count.get(tag, 0) + 1

        return {
            "total_sops": len(sops),
            "sop_ids": [sop.sop_id for sop in sops],
            "unique_tags": list(tags_count.keys()),
            "tags_count": tags_count,
            "storage_path": str(self.storage_path),
            "cache_enabled": self._cache is not None,
            "last_cache_update": self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }

    def _load_from_disk(self) -> List[SOP]:
        """Load SOPs from disk."""
        try:
            if not self.storage_path.exists():
                return []

            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            sops = [SOP(**sop_data) for sop_data in data]
            return sops

        except Exception as e:
            logger.error(f"Failed to load SOPs from disk: {e}")
            return []

    def _write_to_disk(self, sops: List[SOP]):
        """Write SOPs to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(
                    [sop.model_dump() for sop in sops],
                    f,
                    indent=2
                )

        except Exception as e:
            logger.error(f"Failed to write SOPs to disk: {e}")
            raise


def initialize_sample_repository(repo: SOPRepository, sample_sops: List[SOP]) -> int:
    """
    Initialize repository with sample SOPs.

    Args:
        repo: SOPRepository instance
        sample_sops: List of sample SOPs to add

    Returns:
        Number of SOPs added
    """
    added_count = 0

    for sop in sample_sops:
        if repo.create(sop):
            added_count += 1

    logger.info(f"Initialized repository with {added_count} sample SOPs")
    return added_count
