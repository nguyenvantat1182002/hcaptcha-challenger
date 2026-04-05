# -*- coding: utf-8 -*-
import json
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


# Common modern Windows fonts to improve trust score
# From https://camoufox.com/fingerprint/fonts/#new-fonts
COMMON_WINDOWS_FONTS = [
    "Segoe UI", "Segoe UI Web (West European)", "Segoe UI Historic", "Segoe UI Symbol",
    "Helvetica", "Arial", "Verdana", "Tahoma", "Trebuchet MS", "Times New Roman",
    "Georgia", "Courier New", "Impact", "Comic Sans MS", "Segoe Print", "Segoe Script",
    "Gabriola", "Palatino Linotype", "Book Antiqua", "Lucida Sans Unicode", "Lucida Console"
]


# Common Golden WebGL Renderer combinations for Windows (Firefox)
# Based on Camoufox WebGL Research (Jan 2025)
# Note: Exact strings required to match Camoufox webgl_data.db
GOLDEN_WEBGL_PROFILES = [
    {
        "name": "NVIDIA_GTX_980",
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 980 Direct3D11 vs_5_0 ps_5_0), or similar",
        "weight": 35
    },
    {
        "name": "INTEL_HD_GENERIC",
        "vendor": "Google Inc. (Intel)",
        "renderer": "ANGLE (Intel, Intel(R) HD Graphics Direct3D11 vs_5_0 ps_5_0), or similar",
        "weight": 30
    },
    {
        "name": "INTEL_HD_400",
        "vendor": "Google Inc. (Intel)",
        "renderer": "ANGLE (Intel, Intel(R) HD Graphics 400 Direct3D11 vs_5_0 ps_5_0), or similar",
        "weight": 25
    },
    {
        "name": "AMD_RADEON_HD_3200",
        "vendor": "Google Inc. (AMD)",
        "renderer": "ANGLE (AMD, Radeon HD 3200 Graphics Direct3D11 vs_5_0 ps_5_0), or similar",
        "weight": 10
    }
]


# Windows Firefox navigator profiles
# Weighted by real-world hardware distribution for desktop Firefox users
WINDOWS_NAVIGATOR_PROFILES = [
    {
        "name": "WIN10_MODERN",
        "navigator.hardwareConcurrency": 8,
        "navigator.platform": "Win32",
        "navigator.oscpu": "Windows NT 10.0; Win64; x64",
        "navigator.maxTouchPoints": 0,
        "weight": 40
    },
    {
        "name": "WIN10_MID",
        "navigator.hardwareConcurrency": 4,
        "navigator.platform": "Win32",
        "navigator.oscpu": "Windows NT 10.0; Win64; x64",
        "navigator.maxTouchPoints": 0,
        "weight": 35
    },
    {
        "name": "WIN11_MODERN",
        "navigator.hardwareConcurrency": 12,
        "navigator.platform": "Win32",
        "navigator.oscpu": "Windows NT 10.0; Win64; x64",
        "navigator.maxTouchPoints": 0,
        "weight": 15
    },
    {
        "name": "WIN10_LOW",
        "navigator.hardwareConcurrency": 2,
        "navigator.platform": "Win32",
        "navigator.oscpu": "Windows NT 10.0; Win64; x64",
        "navigator.maxTouchPoints": 0,
        "weight": 10
    }
]


def _select_weighted(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Select a profile from a list using weighted random choice."""
    weights = [p["weight"] for p in profiles]
    return random.choices(profiles, weights=weights, k=1)[0]


def _generate_navigator_config(nav_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate navigator fingerprint properties from a profile."""
    return {
        "navigator.hardwareConcurrency": nav_profile["navigator.hardwareConcurrency"],
        "navigator.platform": nav_profile["navigator.platform"],
        "navigator.oscpu": nav_profile["navigator.oscpu"],
        "navigator.maxTouchPoints": nav_profile["navigator.maxTouchPoints"],
    }


def _generate_media_config() -> Dict[str, Any]:
    """
    Generate realistic media device and AudioContext properties.

    Distributions based on typical Windows desktop usage:
    - Most desktops have 1 speaker output, 0-1 microphones, 0-1 webcams
    - AudioContext: 48kHz is the most common sample rate on Windows
    """
    return {
        # Media devices — realistic counts for a typical desktop
        "mediaDevices:enabled": True,
        "mediaDevices:micros": random.choice([0, 1, 1, 1, 2]),
        "mediaDevices:speakers": random.choice([1, 1, 1, 2, 2]),
        "mediaDevices:webcams": random.choice([0, 0, 1, 1, 1]),
        # AudioContext — standard desktop values
        "AudioContext:sampleRate": random.choice([44100, 48000, 48000, 48000]),
        "AudioContext:outputLatency": round(random.uniform(0.005, 0.02), 4),
        "AudioContext:maxChannelCount": random.choice([2, 2, 6, 8]),
    }


def _generate_canvas_config() -> Dict[str, Any]:
    """Generate canvas and font fingerprint noise properties."""
    return {
        "fonts:spacing_seed": random.randint(0, 1073741823),
        "canvas:aaOffset": random.randint(-50, 50),
        "canvas:aaCapOffset": True,
    }


def validate_fingerprint_consistency(config: Dict[str, Any]) -> List[str]:
    """
    Validate cross-dimension consistency of a fingerprint config.
    Returns list of warning messages. Empty list means all checks passed.
    """
    warnings = []
    cfg = config.get("config", {})

    # OS vs Navigator consistency
    if config.get("os") == "windows":
        if cfg.get("navigator.platform") != "Win32":
            warnings.append(
                f"OS is windows but platform is {cfg.get('navigator.platform')}"
            )
        oscpu = cfg.get("navigator.oscpu", "")
        if "Windows" not in oscpu:
            warnings.append(f"OS is windows but oscpu is '{oscpu}'")

    # Hardware sanity
    cores = cfg.get("navigator.hardwareConcurrency", 0)
    if cores < 2:
        warnings.append(
            f"hardwareConcurrency={cores} is unusually low for modern machines"
        )

    # Media device sanity
    webcams = cfg.get("mediaDevices:webcams", 0)
    micros = cfg.get("mediaDevices:micros", 0)
    if webcams > 0 and micros == 0:
        warnings.append("Has webcam but no microphone — unusual combination")

    return warnings


def load_persistent_fingerprint(user_data_dir: str) -> Optional[Dict[str, Any]]:
    """
    Loads a saved fingerprint configuration from the user data directory.
    """
    config_path = Path(user_data_dir).joinpath("fingerprint.json")
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # RECOVERY: Clear old broken config and regenerate if found
                # (Especially for fixed 400 profiles which had the wrong string)
                if "webgl_config" in data and "INTEL_HD_400" in str(data.get("webgl_config")):
                    # If it doesn't have the ", or similar" suffix, it will fail
                    if not str(data["webgl_config"][1]).endswith("similar"):
                        logger.warning("Clearing legacy invalid INTEL_HD_400 profile")
                        return None

                # MIGRATION: Old configs without block_webrtc or navigator props
                # should be regenerated to pick up new dimensions
                if "block_webrtc" not in data:
                    logger.info("Regenerating fingerprint: missing new dimensions (block_webrtc)")
                    return None

                # Cleanup: remove _session_id if it leaked into config dict
                if "config" in data and "_session_id" in data.get("config", {}):
                    del data["config"]["_session_id"]

                # Ensure i_know_what_im_doing is always set
                data.setdefault("i_know_what_im_doing", True)

                logger.debug(f"Loaded persistent fingerprint from {config_path}")
                return data
        except Exception as e:
            logger.warning(f"Failed to load persistent fingerprint: {e}")
    return None


def save_persistent_fingerprint(user_data_dir: str, config: Dict[str, Any]):
    """
    Saves the fingerprint configuration to the user data directory.
    Converts tuples to lists for JSON serialization.
    """
    config_path = Path(user_data_dir).joinpath("fingerprint.json")
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert tuples to lists for JSON serialization
        serializable = {}
        for k, v in config.items():
            if isinstance(v, tuple):
                serializable[k] = list(v)
            else:
                serializable[k] = v

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved persistent fingerprint to {config_path}")
    except Exception as e:
        logger.error(f"Failed to save persistent fingerprint: {e}")


def get_optimized_fingerprint_config(
    user_data_dir: Optional[str] = None,
    use_persistence: bool = True
) -> Dict[str, Any]:
    """
    Generates or loads an optimized fingerprint configuration for Camoufox.

    Returns a dict of kwargs that can be spread into AsyncCamoufox(**config):
    - os: "windows"
    - webgl_config: (vendor, renderer) tuple
    - fonts: list of font family names
    - block_webrtc: True (prevent real IP leak)
    - config: dict of Camoufox C++ level fingerprint properties
      - navigator.* (hardwareConcurrency, platform, oscpu, maxTouchPoints)
      - mediaDevices:* (enabled, micros, speakers, webcams)
      - AudioContext:* (sampleRate, outputLatency, maxChannelCount)
      - fonts:spacing_seed, canvas:aaOffset, canvas:aaCapOffset

    Note: locale/timezone/geolocation are NOT set here — they should be
    handled by Camoufox's geoip=True parameter to match the proxy IP.
    HTTP headers (User-Agent, Accept-Language) are auto-populated by
    Camoufox to match navigator properties.
    """
    # 1. Try to load from persistence
    if use_persistence and user_data_dir:
        saved_config = load_persistent_fingerprint(user_data_dir)
        if saved_config:
            # Restore webgl_config tuple from JSON list
            if "webgl_config" in saved_config and isinstance(saved_config["webgl_config"], list):
                saved_config["webgl_config"] = tuple(saved_config["webgl_config"])
            return saved_config

    # 2. Select profiles using weighted random
    webgl_profile = _select_weighted(GOLDEN_WEBGL_PROFILES)
    nav_profile = _select_weighted(WINDOWS_NAVIGATOR_PROFILES)

    # 3. Build the complete configuration
    config_inner: Dict[str, Any] = {}

    # Session tracking (kept outside config dict — Camoufox validates config keys)
    session_id = str(uuid.uuid4())[:8]

    # Navigator properties
    config_inner.update(_generate_navigator_config(nav_profile))

    # Media devices and AudioContext
    config_inner.update(_generate_media_config())

    # Canvas and font noise
    config_inner.update(_generate_canvas_config())

    # 4. Assemble top-level kwargs for AsyncCamoufox
    full_options: Dict[str, Any] = {
        "os": "windows",
        "webgl_config": (webgl_profile["vendor"], webgl_profile["renderer"]),
        "fonts": COMMON_WINDOWS_FONTS,
        "block_webrtc": True,
        "i_know_what_im_doing": True,
        "config": config_inner,
    }

    logger.debug(
        f"Generated fingerprint profile: "
        f"webgl={webgl_profile['name']}, nav={nav_profile['name']}, "
        f"cores={nav_profile['navigator.hardwareConcurrency']}, "
        f"session={session_id}"
    )

    # 5. Validate cross-dimension consistency
    warnings = validate_fingerprint_consistency(full_options)
    if warnings:
        for w in warnings:
            logger.warning(f"Fingerprint consistency issue: {w}")

    # 6. Save if persistence is requested
    if use_persistence and user_data_dir:
        save_persistent_fingerprint(user_data_dir, full_options)

    return full_options
