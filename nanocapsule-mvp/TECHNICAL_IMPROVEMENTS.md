# Technical Improvements Plan - Nanocapsule Designer

## 🎯 Overview
This document outlines technical improvements to enhance code quality, maintainability, and performance without expanding the scientific scope of the project.

---

## 🧹 Phase 1: Immediate Cleanup (5 minutes)

### File Organization
```bash
# Move misplaced analysis scripts
mkdir -p scripts/analysis
mv Input/Enzimas/calculate_*.py scripts/analysis/
mv Input/Enzimas/volume_comparison_analysis.py scripts/analysis/
mv Input/Enzimas/fast_vdw_volume.py scripts/analysis/
mv Input/Enzimas/vdw_volumes_results.txt scripts/analysis/

# Clean up temporary files
rm -f src/web/radio_interno.txt

# Preserve original HTML as reference
mkdir -p src/web/static/assets
cp ngl-viewer.html src/web/static/assets/reference.html

# Update .gitignore to exclude new temp locations
echo "scripts/analysis/*.txt" >> .gitignore
echo "temp/" >> .gitignore
```

### Files to Clean
- [x] Input/Enzimas/ contains analysis scripts (should be in scripts/)
- [x] src/web/radio_interno.txt is a temporary file
- [x] ngl-viewer.html should be preserved as reference

---

## ⚙️ Phase 2: Configuration Centralization (30 minutes)

### Problem
- 14+ hardcoded paths like `"../../Input"` in app.py
- Configuration scattered across multiple files
- No single source of truth for paths and settings

### Solution: Central Path Management

#### Create `src/config/path_manager.py`
```python
"""
Centralized path management for the entire application.
Replaces all hardcoded paths with configurable ones.
"""
import os
from pathlib import Path
from typing import Dict, Any
import yaml

class PathManager:
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent.parent.parent
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        if config_path is None:
            config_path = self.base_dir / "config" / "default.yaml"

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @property
    def input_capsids(self) -> Path:
        return self.base_dir / self.config['library']['capsides_dir']

    @property
    def input_enzymes(self) -> Path:
        return self.base_dir / self.config['library']['enzymes_dir']

    @property
    def output_base(self) -> Path:
        return self.base_dir / self.config['library']['output_dir']

    @property
    def temp_dir(self) -> Path:
        temp_path = self.base_dir / self.config.get('io', {}).get('temp_dir', './temp')
        temp_path.mkdir(exist_ok=True)
        return temp_path

    def get_structure_fetcher_path(self) -> str:
        """Returns the path for StructureFetcher initialization"""
        return str(self.base_dir / "Input")

    def get_output_path(self, *args) -> Path:
        """Build output paths dynamically"""
        return self.output_base.joinpath(*args)

# Global instance
paths = PathManager()
```

#### Update `config/default.yaml`
```yaml
# Add absolute path configuration
paths:
  # Relative to project root
  input_base: "./Input"
  output_base: "./Output"
  temp_base: "./temp"
  static_assets: "./src/web/static"

# Existing configuration stays the same...
```

#### Refactor `app.py` to use PathManager
```python
# Replace all instances of:
# fetcher = StructureFetcher("../../Input")
# With:
# fetcher = StructureFetcher(paths.get_structure_fetcher_path())

# Replace all instances of:
# output_base_dir="../../Output"
# With:
# output_base_dir=str(paths.output_base)
```

### Files to Update
- [x] src/web/app.py (14 path references)
- [x] src/core/experiment_manager.py (2 path references)
- [x] config/default.yaml (add paths section)

---

## 🛡️ Phase 3: Error Handling System (1 hour)

### Problem
- Generic try/except blocks throughout codebase
- Inconsistent error messages
- No structured logging
- Poor error debugging information

### Solution: Centralized Error Management

#### Create `src/api/errors.py`
```python
"""
Centralized error handling for the Flask application.
Provides consistent error responses and logging.
"""
import logging
from flask import jsonify
from typing import Dict, Any
import traceback

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nanocapsule.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NanocapsuleError(Exception):
    """Base exception for nanocapsule-specific errors"""
    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class StructureNotFoundError(NanocapsuleError):
    def __init__(self, structure_name: str, structure_type: str):
        message = f"{structure_type.title()} '{structure_name}' not found"
        super().__init__(message, 404, {"structure": structure_name, "type": structure_type})

class ExperimentError(NanocapsuleError):
    def __init__(self, message: str, experiment_details: Dict[str, Any] = None):
        super().__init__(message, 400, experiment_details or {})

class SystemResourceError(NanocapsuleError):
    def __init__(self, resource: str, current_usage: float, max_allowed: float):
        message = f"System {resource} usage too high: {current_usage}% (max: {max_allowed}%)"
        super().__init__(message, 503, {"resource": resource, "usage": current_usage})

def handle_nanocapsule_error(error: NanocapsuleError):
    """Handle custom application errors"""
    logger.error(f"NanocapsuleError: {error.message}", extra=error.details)
    response = {
        "error": error.message,
        "status_code": error.status_code
    }
    if error.details:
        response["details"] = error.details

    return jsonify(response), error.status_code

def handle_generic_error(error: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(error)}\n{traceback.format_exc()}")
    return jsonify({
        "error": "An internal error occurred",
        "status_code": 500
    }), 500

def log_api_call(endpoint: str, params: Dict[str, Any], user_id: str = None):
    """Log API calls for debugging"""
    logger.info(f"API call: {endpoint}", extra={
        "endpoint": endpoint,
        "params": params,
        "user_id": user_id
    })
```

#### Create `src/api/validators.py`
```python
"""
Input validation for API endpoints.
Uses marshmallow for robust validation.
"""
from marshmallow import Schema, fields, validate, ValidationError

class ExperimentRequestSchema(Schema):
    capsid = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    enzyme = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    n_enzymes = fields.Int(validate=validate.Range(min=1, max=100), missing=10)
    n_replicas = fields.Int(validate=validate.Range(min=1, max=20), missing=7)
    run_packing = fields.Bool(missing=False)

class RadiusCalculationSchema(Schema):
    capsid = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    force_recalculate = fields.Bool(missing=False)

def validate_request(schema_class):
    """Decorator for request validation"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask import request
            schema = schema_class()
            try:
                validated_data = schema.load(request.get_json() or {})
                return func(validated_data, *args, **kwargs)
            except ValidationError as err:
                from src.api.errors import NanocapsuleError
                raise NanocapsuleError(f"Validation error: {err.messages}", 400)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
```

### Files to Create
- [x] src/api/errors.py
- [x] src/api/validators.py
- [x] src/api/__init__.py

### Files to Update
- [x] src/web/app.py (replace try/except blocks)

---

## ⚡ Phase 4: Performance Optimizations (45 minutes)

### Problem
- StructureFetcher recreated on every request
- No caching of expensive operations
- Temporary files not cleaned automatically
- No resource usage monitoring

### Solution: Smart Caching and Resource Management

#### Create `src/services/cache_service.py`
```python
"""
Caching service for expensive operations.
"""
from functools import lru_cache
from typing import Dict, List
import time
import threading
import os
import glob
from pathlib import Path

class CacheService:
    def __init__(self):
        self._structure_cache = {}
        self._radius_cache = {}
        self._last_cleanup = time.time()

    @lru_cache(maxsize=1)
    def get_structure_fetcher(self):
        """Cached structure fetcher instance"""
        from src.config.path_manager import paths
        from src.io.structure_fetcher import StructureFetcher
        return StructureFetcher(paths.get_structure_fetcher_path())

    def get_available_structures(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """Cache available structures list"""
        cache_key = "available_structures"

        if not force_refresh and cache_key in self._structure_cache:
            cached_time, data = self._structure_cache[cache_key]
            if time.time() - cached_time < 300:  # 5 min cache
                return data

        fetcher = self.get_structure_fetcher()
        data = {
            "capsids": fetcher.list_available_capsides(),
            "enzymes": fetcher.list_available_enzymes()
        }

        self._structure_cache[cache_key] = (time.time(), data)
        return data

    def get_cached_radius(self, capsid: str) -> float:
        """Get cached radius calculation"""
        return self._radius_cache.get(capsid)

    def cache_radius(self, capsid: str, radius: float):
        """Cache radius calculation"""
        self._radius_cache[capsid] = radius

    def cleanup_temp_files(self):
        """Clean temporary files older than 24 hours"""
        current_time = time.time()

        # Only cleanup once per hour
        if current_time - self._last_cleanup < 3600:
            return

        from src.config.path_manager import paths
        temp_dir = paths.temp_dir

        if temp_dir.exists():
            for file_path in temp_dir.glob("*"):
                try:
                    if current_time - file_path.stat().st_mtime > 86400:  # 24 hours
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            import shutil
                            shutil.rmtree(file_path)
                except Exception as e:
                    # Log but don't fail
                    import logging
                    logging.warning(f"Could not clean temp file {file_path}: {e}")

        self._last_cleanup = current_time

# Global cache instance
cache_service = CacheService()

# Background cleanup thread
def start_cleanup_thread():
    def cleanup_loop():
        while True:
            try:
                cache_service.cleanup_temp_files()
                time.sleep(3600)  # Check every hour
            except Exception as e:
                import logging
                logging.error(f"Cleanup thread error: {e}")
                time.sleep(3600)

    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
```

#### Create `src/services/health_service.py`
```python
"""
System health monitoring service.
"""
import psutil
import shutil
from pathlib import Path
from typing import Dict, Any

class HealthService:
    def __init__(self):
        self.max_memory_percent = 85
        self.max_cpu_percent = 90
        self.min_disk_space_gb = 1

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "status": self._get_overall_status(),
            "memory": self._get_memory_status(),
            "cpu": self._get_cpu_status(),
            "disk": self._get_disk_status(),
            "dependencies": self._get_dependency_status(),
            "structures": self._get_structure_status()
        }

    def _get_overall_status(self) -> str:
        """Determine overall system health"""
        memory = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=1)

        if memory > self.max_memory_percent or cpu > self.max_cpu_percent:
            return "overloaded"
        elif not self._check_packmol() or not self._check_pymol():
            return "dependencies_missing"
        else:
            return "healthy"

    def _get_memory_status(self) -> Dict[str, Any]:
        memory = psutil.virtual_memory()
        return {
            "percent_used": memory.percent,
            "available_gb": memory.available / (1024**3),
            "status": "ok" if memory.percent < self.max_memory_percent else "high"
        }

    def _get_cpu_status(self) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=1)
        return {
            "percent_used": cpu_percent,
            "core_count": psutil.cpu_count(),
            "status": "ok" if cpu_percent < self.max_cpu_percent else "high"
        }

    def _get_disk_status(self) -> Dict[str, Any]:
        disk = shutil.disk_usage(".")
        free_gb = disk.free / (1024**3)
        return {
            "free_gb": free_gb,
            "total_gb": disk.total / (1024**3),
            "status": "ok" if free_gb > self.min_disk_space_gb else "low"
        }

    def _check_packmol(self) -> bool:
        """Check if Packmol is available"""
        try:
            import subprocess
            result = subprocess.run(["packmol"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_pymol(self) -> bool:
        """Check if PyMOL is available"""
        try:
            import pymol
            return True
        except ImportError:
            return False

    def _get_dependency_status(self) -> Dict[str, bool]:
        return {
            "packmol": self._check_packmol(),
            "pymol": self._check_pymol()
        }

    def _get_structure_status(self) -> Dict[str, Any]:
        """Get structure library status"""
        from src.services.cache_service import cache_service
        try:
            structures = cache_service.get_available_structures()
            return {
                "capsids_count": len(structures["capsids"]),
                "enzymes_count": len(structures["enzymes"]),
                "status": "ok"
            }
        except Exception as e:
            return {
                "capsids_count": 0,
                "enzymes_count": 0,
                "status": "error",
                "error": str(e)
            }

    def check_resources_available(self):
        """Raise exception if system resources are too high"""
        memory = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent(interval=1)

        if memory > self.max_memory_percent:
            from src.api.errors import SystemResourceError
            raise SystemResourceError("memory", memory, self.max_memory_percent)

        if cpu > self.max_cpu_percent:
            from src.api.errors import SystemResourceError
            raise SystemResourceError("cpu", cpu, self.max_cpu_percent)

# Global health service
health_service = HealthService()
```

### Files to Create
- [x] src/services/cache_service.py
- [x] src/services/health_service.py
- [x] src/services/__init__.py

---

## 🏗️ Phase 5: API Refactoring (1.5 hours)

### Problem
- Single large app.py file with mixed responsibilities
- Business logic mixed with routing
- No separation of concerns
- Hard to test individual components

### Solution: Service Layer Architecture

#### Create `src/api/routes.py`
```python
"""
Clean API routes with minimal logic.
All business logic delegated to services.
"""
from flask import Blueprint, request, jsonify
from src.api.validators import validate_request, ExperimentRequestSchema, RadiusCalculationSchema
from src.api.errors import log_api_call
from src.services.structure_service import structure_service
from src.services.experiment_service import experiment_service
from src.services.health_service import health_service

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/health')
def health_check():
    """System health check endpoint"""
    return jsonify(health_service.get_system_status())

@api.route('/library/capsides')
def get_capsides():
    """Get available capsids"""
    log_api_call("get_capsides", {})
    capsides = structure_service.get_available_capsides()
    return jsonify(capsides)

@api.route('/library/enzymes')
def get_enzymes():
    """Get available enzymes"""
    log_api_call("get_enzymes", {})
    enzymes = structure_service.get_available_enzymes()
    return jsonify(enzymes)

@api.route('/library/combinations')
def get_combinations():
    """Get all possible capsid-enzyme combinations"""
    log_api_call("get_combinations", {})
    combinations = structure_service.get_all_combinations()
    return jsonify(combinations)

@api.route('/radius/<capsid>')
def calculate_radius(capsid):
    """Calculate internal radius for capsid"""
    log_api_call("calculate_radius", {"capsid": capsid})
    radius = structure_service.calculate_capsid_radius(capsid)
    return jsonify({"capsid": capsid, "radius": radius})

@api.route('/experiment/run', methods=['POST'])
@validate_request(ExperimentRequestSchema)
def run_experiment(validated_data):
    """Run packing experiment"""
    log_api_call("run_experiment", validated_data)

    # Check system resources before starting
    health_service.check_resources_available()

    result = experiment_service.run_experiment(**validated_data)
    return jsonify(result)

@api.route('/download/<experiment_id>')
def download_results(experiment_id):
    """Download experiment results"""
    log_api_call("download_results", {"experiment_id": experiment_id})
    return experiment_service.create_download_package(experiment_id)
```

#### Create `src/services/structure_service.py`
```python
"""
Service for structure-related operations.
Handles capsids, enzymes, and their combinations.
"""
from typing import List, Dict, Any, Tuple
from src.services.cache_service import cache_service
from src.api.errors import StructureNotFoundError
import logging

logger = logging.getLogger(__name__)

class StructureService:
    def __init__(self):
        self.fetcher = None

    def _get_fetcher(self):
        """Get cached structure fetcher"""
        if self.fetcher is None:
            self.fetcher = cache_service.get_structure_fetcher()
        return self.fetcher

    def get_available_capsides(self, force_refresh: bool = False) -> List[str]:
        """Get list of available capsids"""
        structures = cache_service.get_available_structures(force_refresh)
        return structures["capsids"]

    def get_available_enzymes(self, force_refresh: bool = False) -> List[str]:
        """Get list of available enzymes"""
        structures = cache_service.get_available_structures(force_refresh)
        return structures["enzymes"]

    def get_all_combinations(self) -> List[Dict[str, str]]:
        """Get all possible capsid-enzyme combinations"""
        capsids = self.get_available_capsides()
        enzymes = self.get_available_enzymes()

        combinations = []
        for capsid in capsids:
            for enzyme in enzymes:
                combinations.append({
                    "capsid": capsid,
                    "enzyme": enzyme,
                    "id": f"{capsid}_{enzyme}"
                })

        return combinations

    def calculate_capsid_radius(self, capsid: str, force_recalculate: bool = False) -> float:
        """Calculate internal radius for capsid"""
        # Check cache first
        if not force_recalculate:
            cached_radius = cache_service.get_cached_radius(capsid)
            if cached_radius is not None:
                logger.info(f"Using cached radius for {capsid}: {cached_radius}")
                return cached_radius

        # Verify capsid exists
        if capsid not in self.get_available_capsides():
            raise StructureNotFoundError(capsid, "capsid")

        # Calculate radius
        fetcher = self._get_fetcher()
        capsid_path = fetcher.get_structure_path("capside", capsid)

        if not capsid_path:
            raise StructureNotFoundError(capsid, "capsid")

        # Use existing radius calculation logic
        from src.core.capsid import Capsid
        capsid_obj = Capsid(capsid_path)
        radius = capsid_obj.calculate_internal_radius()

        # Cache the result
        cache_service.cache_radius(capsid, radius)
        logger.info(f"Calculated radius for {capsid}: {radius}")

        return radius

    def get_structure_paths(self, capsid: str, enzyme: str) -> Tuple[str, str]:
        """Get file paths for capsid and enzyme"""
        fetcher = self._get_fetcher()

        capsid_path = fetcher.get_structure_path("capside", capsid)
        enzyme_path = fetcher.get_structure_path("enzima", enzyme)

        if not capsid_path:
            raise StructureNotFoundError(capsid, "capsid")
        if not enzyme_path:
            raise StructureNotFoundError(enzyme, "enzyme")

        return capsid_path, enzyme_path

# Global service instance
structure_service = StructureService()
```

#### Create `src/services/experiment_service.py`
```python
"""
Service for experiment-related operations.
Handles packing experiments and result management.
"""
from typing import Dict, Any
import logging
from pathlib import Path
import uuid
import zipfile
import io
from flask import send_file

from src.services.structure_service import structure_service
from src.api.errors import ExperimentError
from src.config.path_manager import paths

logger = logging.getLogger(__name__)

class ExperimentService:
    def __init__(self):
        self.active_experiments = {}

    def run_experiment(self, capsid: str, enzyme: str, n_enzymes: int = None,
                      n_replicas: int = 7, run_packing: bool = False) -> Dict[str, Any]:
        """Run a packing experiment"""
        experiment_id = str(uuid.uuid4())

        logger.info(f"Starting experiment {experiment_id}: {capsid} + {enzyme}")

        try:
            # Validate structures exist
            capsid_path, enzyme_path = structure_service.get_structure_paths(capsid, enzyme)

            # Get radius
            radius = structure_service.calculate_capsid_radius(capsid)

            if not run_packing:
                # Just return setup information
                return {
                    "experiment_id": experiment_id,
                    "capsid": capsid,
                    "enzyme": enzyme,
                    "capsid_path": capsid_path,
                    "enzyme_path": enzyme_path,
                    "internal_radius": radius,
                    "n_replicas": n_replicas,
                    "status": "configured"
                }

            # Run actual packing
            result = self._run_packing_experiment(
                experiment_id, capsid_path, enzyme_path,
                n_enzymes, n_replicas, radius
            )

            # Store result for download
            self.active_experiments[experiment_id] = result

            return {
                "experiment_id": experiment_id,
                "status": "completed",
                **result
            }

        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed: {str(e)}")
            raise ExperimentError(f"Experiment failed: {str(e)}", {
                "experiment_id": experiment_id,
                "capsid": capsid,
                "enzyme": enzyme
            })

    def _run_packing_experiment(self, experiment_id: str, capsid_path: str,
                               enzyme_path: str, n_enzymes: int, n_replicas: int,
                               radius: float) -> Dict[str, Any]:
        """Execute the actual packing experiment"""
        from src.core.config import ConfigManager
        from src.core.experiment_runner import ExperimentRunner

        config = ConfigManager()
        runner = ExperimentRunner(output_base_dir=str(paths.output_base), config=config)

        # Run the experiment using existing logic
        if n_enzymes:
            # Fixed number packing
            results = runner.run_fixed_packing(
                capsid_file=capsid_path,
                enzyme_file=enzyme_path,
                n_enzymes=n_enzymes,
                n_replicas=n_replicas
            )
        else:
            # Maximum packing
            results = runner.run_maximum_packing(
                capsid_file=capsid_path,
                enzyme_file=enzyme_path,
                n_replicas=n_replicas
            )

        return {
            "results": results,
            "internal_radius": radius,
            "experiment_id": experiment_id
        }

    def create_download_package(self, experiment_id: str):
        """Create downloadable ZIP package for experiment"""
        if experiment_id not in self.active_experiments:
            raise ExperimentError(f"Experiment {experiment_id} not found")

        experiment_data = self.active_experiments[experiment_id]

        # Create in-memory ZIP
        memory_file = io.BytesIO()

        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add experiment results
            if "results" in experiment_data:
                # Add PDB files, logs, etc.
                self._add_experiment_files_to_zip(zf, experiment_data)

            # Add metadata
            import json
            metadata = {
                "experiment_id": experiment_id,
                "timestamp": experiment_data.get("timestamp"),
                "parameters": experiment_data.get("parameters", {})
            }
            zf.writestr("metadata.json", json.dumps(metadata, indent=2))

        memory_file.seek(0)

        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f"experiment_{experiment_id}.zip",
            mimetype='application/zip'
        )

    def _add_experiment_files_to_zip(self, zf: zipfile.ZipFile, experiment_data: Dict[str, Any]):
        """Add experiment files to ZIP archive"""
        # Implementation details for adding files to ZIP
        # This would include PDB files, logs, statistics, etc.
        pass

# Global service instance
experiment_service = ExperimentService()
```

### Files to Create
- [x] src/api/routes.py
- [x] src/services/structure_service.py
- [x] src/services/experiment_service.py
- [x] src/config/path_manager.py

### Files to Update
- [x] src/web/app.py (convert to use new architecture)

---

## 📋 Implementation Timeline

### Week 1: Foundation
- **Day 1**: Phase 1 (Cleanup) + Phase 2 (Config) ✅
- **Day 2**: Phase 3 (Error Handling) ✅
- **Day 3**: Phase 4 (Performance) ✅
- **Day 4**: Phase 5 (API Refactoring) ✅
- **Day 5**: Testing + Integration ✅

### Week 2: Polish
- **Day 1-2**: Comprehensive testing
- **Day 3-4**: Documentation updates
- **Day 5**: Performance benchmarking

---

## 🎯 Success Metrics

### Code Quality
- [ ] Zero hardcoded paths in source code
- [ ] All errors use centralized error handling
- [ ] All API endpoints have input validation
- [ ] Structured logging throughout application
- [ ] >90% test coverage for new code

### Performance
- [ ] <500ms response time for structure listings
- [ ] <2s response time for radius calculations (cached)
- [ ] Automatic cleanup of temp files >24h old
- [ ] Memory usage warnings at >85%
- [ ] CPU usage warnings at >90%

### Maintainability
- [ ] Clear separation of concerns (routes/services/core)
- [ ] All services have single responsibility
- [ ] All functions have type hints and docstrings
- [ ] Configuration centralized and documented
- [ ] Health checks for all dependencies

---

## 🚀 Quick Start Commands

### Apply Phase 1 (Immediate Cleanup)
```bash
cd /home/luciernaga/Escritorio/PckerEnzymer/nanocapsule-mvp

# Move analysis scripts
mkdir -p scripts/analysis
mv Input/Enzimas/calculate_*.py scripts/analysis/
mv Input/Enzimas/volume_comparison_analysis.py scripts/analysis/
mv Input/Enzimas/fast_vdw_volume.py scripts/analysis/
mv Input/Enzimas/vdw_volumes_results.txt scripts/analysis/

# Clean temp files
rm -f src/web/radio_interno.txt

# Preserve reference
mkdir -p src/web/static/assets
cp ngl-viewer.html src/web/static/assets/reference.html

echo "Phase 1 complete! ✅"
```

### Install New Dependencies
```bash
pip install marshmallow psutil
```

### Validate Installation
```bash
python -c "
from src.services.cache_service import cache_service
from src.services.health_service import health_service
print('Services loaded successfully!')
print('System status:', health_service.get_system_status()['status'])
"
```

---

## 📝 Notes

- All improvements maintain backward compatibility
- No scientific algorithm changes
- Focus on code quality and maintainability
- Gradual implementation allows for testing at each step
- Can be implemented while system remains operational

---

**Status**: Ready for implementation
**Estimated Total Time**: 8-10 hours across 1 week
**Risk Level**: Low (no breaking changes to core functionality)