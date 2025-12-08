import os
import re
import yaml
from typing import Optional, List
from pathlib import Path
from .logger import get_logger

logger = get_logger(__name__)

def get_plugin_version(plugin_root: str) -> str:
    """Read plugin version from manifest.yaml"""
    manifest_path = os.path.join(plugin_root, 'manifest.yaml')

    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"manifest.yaml not found at {manifest_path}")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
            version = manifest.get('version', '0.0.0')

        if not isinstance(version, str):
            raise ValueError(f"Invalid version format in manifest.yaml: {version}")

        return version
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse manifest.yaml: {e}")
    except Exception as e:
        raise RuntimeError(f"Error reading plugin version: {e}")

def extract_version_from_filename(filename: str) -> Optional[str]:
    """Extract version number from filename"""
    match = re.match(r'echarts-convert-(\d+\.\d+\.\d+)-linux-', filename)
    return match.group(1) if match else None

def find_all_versioned_binaries(bin_dir: str) -> List[str]:
    """Find all versioned binary files"""
    if not os.path.exists(bin_dir):
        return []

    binaries = []
    for file in os.listdir(bin_dir):
        if file.startswith('echarts-convert-') and '.gz' in file:
            version = extract_version_from_filename(file)
            if version:
                binaries.append(file)

    return binaries

def get_latest_version(available_versions: List[str]) -> Optional[str]:
    """Get the latest version number"""
    if not available_versions:
        return None

    def version_tuple(v):
        return tuple(map(int, v.split('.')))

    return max(available_versions, key=version_tuple)

def cleanup_old_binaries(bin_dir: str, target_version: str) -> None:
    """Clean up all binary files except the target version"""
    binaries = find_all_versioned_binaries(bin_dir)

    for binary in binaries:
        # Use precise version extraction and comparison to avoid substring false matches
        binary_version = extract_version_from_filename(binary)
        if binary_version != target_version:
            binary_path = os.path.join(bin_dir, binary)
            try:
                os.remove(binary_path)
                logger.info(f"Removed old binary: {binary}")
            except OSError as e:
                logger.warning(f"Failed to remove {binary}: {e}")

def select_binary_version(bin_dir: str, current_version: str) -> str:
    """Select appropriate binary version"""
    binaries = find_all_versioned_binaries(bin_dir)

    if not binaries:
        raise FileNotFoundError(f"No versioned binaries found in {bin_dir}")

    # Use precise version extraction and comparison to avoid substring false matches
    current_version_binaries = [
        b for b in binaries
        if extract_version_from_filename(b) == current_version
    ]
    if current_version_binaries:
        logger.info(f"Found current version binaries: {current_version_binaries}")
        # Clean up other versions
        cleanup_old_binaries(bin_dir, current_version)
        return current_version

    # If current version not found, select latest version
    available_versions = [extract_version_from_filename(b) for b in binaries]
    available_versions = [v for v in available_versions if v is not None]

    latest_version = get_latest_version(available_versions)
    if latest_version:
        logger.info(f"Current version {current_version} not found, using latest: {latest_version}")
        # Clean up other versions, keep latest version
        cleanup_old_binaries(bin_dir, latest_version)
        return latest_version

    raise FileNotFoundError(f"No valid versioned binaries found")

def get_versioned_binary_name(version: str, arch: str) -> str:
    """Generate versioned binary filename"""
    return f'echarts-convert-{version}-linux-{arch}'