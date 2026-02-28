"""Detect the appropriate FluidSynth audio driver for the current OS."""

import platform


def detect_os_driver() -> str:
    """Return the FluidSynth driver name for the current operating system."""
    system = platform.system()
    if system == "Darwin":
        return "coreaudio"
    elif system == "Linux":
        return "alsa"
    elif system == "Windows":
        return "dsound"
    else:
        return "alsa"  # fallback
