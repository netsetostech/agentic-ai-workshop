"""Load the installed kit planner so teaching examples use its real decisions."""
import hashlib
import importlib.util
from pathlib import Path
import sys


class KitAdapter:
    """Load the installed kit's reconciliation functions directly instead of maintaining a teaching copy.
    
    Example: kit = KitAdapter(config.kit_root); report = evaluate_widget(kit, rows)
    """
    def __init__(self, root):
        """Load reconcile.py and validate its pure decision functions; record its path and content hash.
        
        Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
        """
        self.root = Path(root).resolve()
        self.ingest = self.root / "services" / "ingest"
        self.planner = self._load("reconcile")
        for name in ("plan", "decide_bytes", "drift_of"):
            if not callable(getattr(self.planner, name, None)):
                raise RuntimeError(f"Installed kit reconcile.py has no {name}(). Update the kit explicitly.")
        self.provenance = {
            "path": str(self.ingest / "reconcile.py"),
            "sha256": hashlib.sha256((self.ingest / "reconcile.py").read_bytes()).hexdigest(),
            "implementation": "actual local kit, loaded at runtime",
        }

    def _load(self, name):
        """Import one kit module under a path-specific name without copying its implementation.
        
        Example: self._load('reconcile')
        """
        path = self.ingest / f"{name}.py"
        if not path.is_file():
            raise FileNotFoundError(f"Required kit module is missing: {path}")
        module_name = f"_workshop_kit_{name}_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}"
        if module_name in sys.modules:
            return sys.modules[module_name]
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(module_name, None)
            raise
        return module

