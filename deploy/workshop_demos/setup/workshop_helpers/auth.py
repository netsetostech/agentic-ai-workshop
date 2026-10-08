"""SDK ADC and gcloud identities are separate; no token is logged."""
import shutil
import subprocess


def gcloud(*args, timeout=90):
    """Run gcloud with a bounded wait and return stdout; surface command failures without logging tokens.
    
    Example: gcloud('auth', 'print-identity-token', '--include-email', f'--audiences={audience}', f'--impersonate-service-account={config.ui_service_account}', f'--project={config.project}')
    """
    executable = shutil.which("gcloud")
    if not executable:
        raise RuntimeError("gcloud is not on the IDE process PATH. Run PyCharm in the Cloud Workstation.")
    result = subprocess.run([executable, *args], capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"gcloud {' '.join(args[:3])} failed:\n{result.stderr.strip()}")
    return result.stdout.strip()


def checked_credentials():
    """Refresh Python ADC once with a bounded request; explain missing packages or expired sign-in.
    
    Example: credentials = checked_credentials() before constructing a live SDK client
    """
    try:
        import google.auth
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise RuntimeError("Google libraries are missing in this interpreter. Run setup/bootstrap.py with INSTALL_LIVE_DEPENDENCIES=True.") from exc

    class BoundedRequest(Request):
        """Bound ADC refresh HTTP waits so expired workstation credentials fail with an actionable message.
        
        Example: BoundedRequest()
        """
        def __call__(self, *args, **kwargs):
            """Bound each credential-refresh HTTP request to avoid the default long metadata retry delay.
            
            Example: super().__call__(*args, **kwargs)
            """
            kwargs["timeout"] = 20
            return super().__call__(*args, **kwargs)

    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(BoundedRequest())
    except Exception as exc:
        raise RuntimeError(
            "Python ADC could not refresh. Run setup/authenticate.py on this workstation. "
            "If GOOGLE_APPLICATION_CREDENTIALS is set in your Run Configuration, it selects "
            f"a different credential file. Original error: {exc}"
        ) from exc
    return credentials


def identity_token(config, audience):
    """Mint a fresh audience-bound UI service-account token; never persist the returned credential.
    
    Example: token = identity_token(config, config.api_base_url) in an authenticated request
    """
    return gcloud("auth", "print-identity-token", "--include-email",
                  f"--audiences={audience}",
                  f"--impersonate-service-account={config.ui_service_account}",
                  f"--project={config.project}")
