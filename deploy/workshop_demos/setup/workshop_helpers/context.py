"""One context per demo, with lazy clients and persistent evidence on failure."""
import sys
from .artifacts import ArtifactStore
from .config import load_config


class DemoContext:
    """Provide a scoped preflight with lazy clients, actual kit functions and retained evidence.
    
    Example: with DemoContext("preflight", live=False) as context: print(context.kit)
    """
    def __init__(self, demo, live=False, config=None, module=1, lesson="1.8"):
        """Prepare a single preflight context; defer cloud clients until first use.
        
        Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
        """
        self.config = config or load_config()
        self.live = live
        self.credentials = None
        self._db = self._storage = self._api = self._kit = None
        self.artifacts = ArtifactStore(self.config, demo, module=module, lesson=lesson)

    def __enter__(self):
        """Print the chosen interpreter and refresh ADC only for a live preflight.
        
        Example: Use the owning class with a with statement; context entry/exit invokes this method.
        """
        print("Python:", sys.executable)
        print("Mode:", "LIVE GCP" if self.live else "OFFLINE: simulated inputs, actual kit planner")
        print("Project:", self.config.project or "not needed offline", "| tenant:", self.config.tenant_id)
        print("Results:", self.artifacts.directory, flush=True)
        if self.live:
            from .auth import checked_credentials
            try:
                if not self.config.project:
                    raise ValueError("Set project in setup/config/settings.local.json, or run bootstrap.py.")
                self.credentials = checked_credentials()
            except Exception as exc:
                self.artifacts.finish(exc)
                raise
        return self

    def __exit__(self, kind, error, traceback):
        """Record failure or completion and close opened clients while preserving exceptions.
        
        Example: Use the owning class with a with statement; context entry/exit invokes this method.
        """
        self.artifacts.finish(error)
        for client in (self._db, self._storage):
            close = getattr(client, "close", None)
            if close:
                close()
        print("Evidence saved:", self.artifacts.directory)
        return False

    @property
    def kit(self):
        """Load and record the actual local planner implementation on first use.
        
        Example: self.kit() in the owning lesson/helper context
        """
        if self._kit is None:
            from .kit import KitAdapter
            self._kit = KitAdapter(self.config.kit_root)
            self.artifacts.save("kit_version", self._kit.provenance)
        return self._kit

    @property
    def db(self):
        """Return a lazy Firestore client; reject cloud access in offline mode.
        
        Example: self.db() in the owning lesson/helper context
        """
        if not self.live:
            raise RuntimeError("An offline demo cannot open a cloud client.")
        if self._db is None:
            from google.cloud import firestore
            self._db = firestore.Client(project=self.config.project, credentials=self.credentials)
        return self._db

    @property
    def storage(self):
        """Return a lazy Storage client; reject cloud access in offline mode.
        
        Example: self.storage() in the owning lesson/helper context
        """
        if not self.live:
            raise RuntimeError("An offline demo cannot open a cloud client.")
        if self._storage is None:
            from google.cloud import storage
            self._storage = storage.Client(project=self.config.project, credentials=self.credentials)
        return self._storage

    @property
    def api(self):
        """Return the serving API client and save its nonsecret configuration snapshot.
        
        Example: self.api() in the owning lesson/helper context
        """
        if not self.live:
            raise RuntimeError("An offline demo cannot call the API.")
        if self._api is None:
            from .api import ApiClient
            self._api = ApiClient(self.config)
            from dataclasses import asdict
            self.artifacts.save("api_configuration", asdict(self._api.serving))
        return self._api
