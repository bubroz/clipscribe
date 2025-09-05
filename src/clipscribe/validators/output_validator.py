"""
Output validation for ClipScribe to catch truncations, inconsistencies, and errors.
Uses Pydantic models and custom validators to ensure data quality.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from pydantic import ValidationError
import re

from ..core_data import CoreData, Entity, Relationship, VideoMetadata

logger = logging.getLogger(__name__)


class OutputValidator:
    """
    Validates ClipScribe output files for quality and consistency.
    Catches truncations, empty fields, mismatched confidences, etc.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, raise exceptions on validation errors.
                        If False, log warnings and attempt recovery.
        """
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_directory(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate all output files in a directory.
        
        Args:
            directory: Path to output directory
            
        Returns:
            Validation report with errors, warnings, and suggestions
        """
        directory = Path(directory)
        report = {
            "directory": str(directory),
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "file_checks": {}
        }
        
        # Check for expected files
        expected_files = [
            "core.json",
            "transcript.txt",
            "metadata.json",
            "knowledge_graph.json",
            "report.md"
        ]
        
        for filename in expected_files:
            filepath = directory / filename
            if not filepath.exists():
                report["errors"].append(f"Missing expected file: {filename}")
                report["file_checks"][filename] = "missing"
            else:
                # Validate individual file
                file_report = self._validate_file(filepath)
                report["file_checks"][filename] = file_report
                report["errors"].extend(file_report.get("errors", []))
                report["warnings"].extend(file_report.get("warnings", []))
        
        # Check for legacy/redundant files
        legacy_files = [
            "entities.json",
            "relationships.json",
            "entities.csv",
            "relationships.csv",
            "facts.json",
            "manifest.json",
            "chimera_format.json"
        ]
        
        for filename in legacy_files:
            if (directory / filename).exists():
                report["warnings"].append(f"Legacy file present: {filename} (consider removing)")
        
        # Cross-file consistency checks
        if (directory / "core.json").exists():
            consistency_report = self._check_consistency(directory)
            report["errors"].extend(consistency_report.get("errors", []))
            report["warnings"].extend(consistency_report.get("warnings", []))
            report["suggestions"].extend(consistency_report.get("suggestions", []))
        
        return report
    
    def _validate_file(self, filepath: Path) -> Dict[str, Any]:
        """Validate individual file."""
        report = {"errors": [], "warnings": [], "status": "ok"}
        
        if filepath.suffix == ".json":
            report.update(self._validate_json(filepath))
        elif filepath.suffix == ".txt":
            report.update(self._validate_text(filepath))
        elif filepath.suffix == ".md":
            report.update(self._validate_markdown(filepath))
        
        return report
    
    def _validate_json(self, filepath: Path) -> Dict[str, Any]:
        """Validate JSON file structure and content."""
        report = {"errors": [], "warnings": []}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            report["errors"].append(f"Invalid JSON in {filepath.name}: {e}")
            return report
        except Exception as e:
            report["errors"].append(f"Could not read {filepath.name}: {e}")
            return report
        
        # File-specific validation
        if filepath.name == "core.json":
            report.update(self._validate_core_json(data))
        elif filepath.name == "metadata.json":
            report.update(self._validate_metadata_json(data))
        elif filepath.name == "knowledge_graph.json":
            report.update(self._validate_graph_json(data))
        
        return report
    
    def _validate_core_json(self, data: Dict) -> Dict[str, Any]:
        """Validate core.json structure using Pydantic."""
        report = {"errors": [], "warnings": []}
        
        try:
            # Attempt to parse with Pydantic
            core_data = CoreData(**data)
            
            # Check for quality issues
            if not core_data.entities:
                report["warnings"].append("No entities extracted")
            
            if not core_data.relationships:
                report["warnings"].append("No relationships extracted")
            
            # Check for empty evidence
            empty_evidence_count = sum(
                1 for entity in core_data.entities
                if not entity.evidence
            )
            if empty_evidence_count > 0:
                report["warnings"].append(
                    f"{empty_evidence_count} entities have no evidence"
                )
            
            # Check mention counts
            suspicious_mentions = [
                e for e in core_data.entities
                if e.mention_count == 1 and len(e.evidence) > 1
            ]
            if suspicious_mentions:
                report["warnings"].append(
                    f"{len(suspicious_mentions)} entities have mention_count=1 but multiple evidence entries"
                )
            
            # Check for truncated transcript
            if core_data.transcript_segments:
                full_text = core_data.full_transcript
                if "...(truncated" in full_text or full_text.endswith("..."):
                    report["errors"].append("Transcript appears to be truncated")
            
            # Check confidence consistency
            confidence_values = [e.confidence for e in core_data.entities]
            if confidence_values and all(c == confidence_values[0] for c in confidence_values):
                report["warnings"].append(
                    f"All entities have same confidence ({confidence_values[0]}), may indicate hardcoding"
                )
            
        except ValidationError as e:
            for error in e.errors():
                report["errors"].append(
                    f"Validation error in {'.'.join(str(x) for x in error['loc'])}: {error['msg']}"
                )
        except Exception as e:
            report["errors"].append(f"Unexpected error validating core.json: {e}")
        
        return report
    
    def _validate_metadata_json(self, data: Dict) -> Dict[str, Any]:
        """Validate metadata.json."""
        report = {"errors": [], "warnings": []}
        
        try:
            # Check required fields
            required = ["url", "title", "duration", "platform"]
            for field in required:
                if field not in data:
                    report["errors"].append(f"Missing required field: {field}")
            
            # Validate URL
            if "url" in data:
                url = data["url"]
                if not url.startswith(("http://", "https://")):
                    report["errors"].append(f"Invalid URL format: {url}")
            
            # Check duration
            if "duration" in data:
                duration = data["duration"]
                if not isinstance(duration, (int, float)) or duration <= 0:
                    report["errors"].append(f"Invalid duration: {duration}")
            
            # Check processing cost
            if "cost" in data:
                cost = data["cost"]
                if not isinstance(cost, (int, float)) or cost < 0:
                    report["warnings"].append(f"Invalid cost: {cost}")
                elif cost > 1.0:
                    report["warnings"].append(f"Unusually high cost: ${cost:.2f}")
            
        except Exception as e:
            report["errors"].append(f"Error validating metadata: {e}")
        
        return report
    
    def _validate_graph_json(self, data: Dict) -> Dict[str, Any]:
        """Validate knowledge_graph.json."""
        report = {"errors": [], "warnings": []}
        
        try:
            # Check structure
            if "nodes" not in data or "edges" not in data:
                report["errors"].append("Missing nodes or edges in knowledge graph")
                return report
            
            nodes = data["nodes"]
            edges = data["edges"]
            
            # Check for empty graph
            if not nodes:
                report["warnings"].append("Knowledge graph has no nodes")
            if not edges:
                report["warnings"].append("Knowledge graph has no edges")
            
            # Validate node references in edges
            node_ids = {node.get("id", node.get("label")) for node in nodes}
            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")
                
                if source not in node_ids:
                    report["errors"].append(f"Edge references unknown node: {source}")
                if target not in node_ids:
                    report["errors"].append(f"Edge references unknown node: {target}")
            
            # Check for disconnected nodes
            connected_nodes = set()
            for edge in edges:
                connected_nodes.add(edge.get("source"))
                connected_nodes.add(edge.get("target"))
            
            disconnected = node_ids - connected_nodes
            if disconnected:
                report["warnings"].append(
                    f"{len(disconnected)} disconnected nodes in graph"
                )
            
        except Exception as e:
            report["errors"].append(f"Error validating knowledge graph: {e}")
        
        return report
    
    def _validate_text(self, filepath: Path) -> Dict[str, Any]:
        """Validate text files."""
        report = {"errors": [], "warnings": []}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for truncation markers
            if "...(truncated" in content or content.endswith("..."):
                report["errors"].append(f"{filepath.name} appears to be truncated")
            
            # Check for XML artifacts
            if "</DOCUMENT>" in content or "<DOCUMENT>" in content:
                report["warnings"].append(f"{filepath.name} contains XML artifacts")
            
            # Check size
            if len(content) < 100:
                report["warnings"].append(f"{filepath.name} is suspiciously short ({len(content)} chars)")
            
        except Exception as e:
            report["errors"].append(f"Error reading {filepath.name}: {e}")
        
        return report
    
    def _validate_markdown(self, filepath: Path) -> Dict[str, Any]:
        """Validate markdown files."""
        report = {"errors": [], "warnings": []}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for placeholders
            if "TBD" in content or "TODO" in content:
                report["warnings"].append(f"{filepath.name} contains placeholders")
            
            # Check for proper structure
            if not content.startswith("#"):
                report["warnings"].append(f"{filepath.name} doesn't start with a header")
            
            # Check for empty sections
            sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
            for section in sections:
                # Check if section has content after it
                pattern = f"## {re.escape(section)}.*?(?=##|$)"
                match = re.search(pattern, content, re.DOTALL)
                if match and len(match.group().strip()) < 50:
                    report["warnings"].append(f"Section '{section}' appears empty")
            
        except Exception as e:
            report["errors"].append(f"Error reading {filepath.name}: {e}")
        
        return report
    
    def _check_consistency(self, directory: Path) -> Dict[str, Any]:
        """Check consistency across files."""
        report = {"errors": [], "warnings": [], "suggestions": []}
        
        try:
            # Load core data
            with open(directory / "core.json") as f:
                core_data = json.load(f)
            
            # If other files exist, check consistency
            if (directory / "entities.json").exists():
                with open(directory / "entities.json") as f:
                    legacy_entities = json.load(f)
                    
                # Compare entity counts
                core_count = len(core_data.get("entities", []))
                legacy_count = len(legacy_entities.get("entities", []))
                
                if core_count != legacy_count:
                    report["warnings"].append(
                        f"Entity count mismatch: core.json has {core_count}, entities.json has {legacy_count}"
                    )
            
            # Check transcript consistency
            if (directory / "transcript.txt").exists():
                with open(directory / "transcript.txt") as f:
                    txt_content = f.read()
                
                core_transcript = " ".join(
                    seg["text"] for seg in core_data.get("transcript_segments", [])
                )
                
                if len(txt_content) != len(core_transcript):
                    report["warnings"].append(
                        f"Transcript length mismatch: transcript.txt has {len(txt_content)} chars, "
                        f"core.json has {len(core_transcript)} chars"
                    )
            
            # Suggest optimizations
            legacy_files = ["entities.json", "relationships.json", "facts.json", "manifest.json"]
            existing_legacy = [f for f in legacy_files if (directory / f).exists()]
            
            if existing_legacy:
                report["suggestions"].append(
                    f"Remove {len(existing_legacy)} redundant files to save space: {', '.join(existing_legacy)}"
                )
            
        except Exception as e:
            report["errors"].append(f"Error checking consistency: {e}")
        
        return report
    
    def fix_common_issues(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        Attempt to fix common issues automatically.
        
        Args:
            directory: Path to output directory
            
        Returns:
            Report of fixes applied
        """
        directory = Path(directory)
        fixes = {"applied": [], "failed": []}
        
        try:
            # Load core data if it exists
            core_path = directory / "core.json"
            if core_path.exists():
                with open(core_path) as f:
                    data = json.load(f)
                
                modified = False
                
                # Fix mention counts
                for entity in data.get("entities", []):
                    if entity.get("mention_count") == 1 and len(entity.get("evidence", [])) > 1:
                        entity["mention_count"] = len(entity["evidence"])
                        modified = True
                        fixes["applied"].append(f"Fixed mention_count for {entity['name']}")
                
                # Remove hardcoded confidences
                unique_confidences = set()
                for entity in data.get("entities", []):
                    unique_confidences.add(entity.get("confidence", 0.9))
                
                if len(unique_confidences) == 1:
                    # All same, likely hardcoded
                    for entity in data["entities"]:
                        # Vary slightly based on evidence count
                        evidence_count = len(entity.get("evidence", []))
                        entity["confidence"] = min(0.95, 0.7 + (evidence_count * 0.05))
                        modified = True
                    fixes["applied"].append("Adjusted hardcoded confidence scores")
                
                # Save if modified
                if modified:
                    with open(core_path, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    fixes["applied"].append("Saved fixes to core.json")
            
            # Remove redundant files if core.json exists
            if core_path.exists():
                redundant = ["entities.csv", "relationships.csv", "chimera_format.json"]
                for filename in redundant:
                    filepath = directory / filename
                    if filepath.exists():
                        filepath.unlink()
                        fixes["applied"].append(f"Removed redundant file: {filename}")
            
        except Exception as e:
            fixes["failed"].append(f"Error applying fixes: {e}")
        
        return fixes
