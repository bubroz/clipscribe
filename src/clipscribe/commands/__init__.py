"""ClipScribe CLI commands module."""


# Lazy import CLI only when needed - don't import at package level
def get_cli():
    """Get CLI instance with lazy loading."""
    from .cli import cli

    return cli


__all__ = ["get_cli"]
