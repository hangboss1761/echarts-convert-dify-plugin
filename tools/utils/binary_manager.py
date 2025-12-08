"""
Binary Manager Module

Handles decompression and management of compressed binary executables with version support.
"""

import os
import shutil
from typing import Optional, List
from dify_plugin.errors.model import InvokeError
from .version_manager import get_plugin_version, select_binary_version
from .logger import get_logger

logger = get_logger(__name__)


class BinaryManager:
    """Manages compressed binary executables with version-aware path deployment"""

    def _get_available_temp_directory(self) -> str:
        """Select available temporary directory, prioritize plugin tmp, fallback to system tmp"""
        # Try plugin root tmp directory first
        plugin_tmp = os.path.join(self.plugin_root, 'tmp')
        if self._test_directory_permissions(plugin_tmp):
            logger.info(f"Using plugin tmp directory: {plugin_tmp}")
            return plugin_tmp

        # Fallback to system /tmp/echarts-convert
        system_tmp = '/tmp/echarts-convert'
        if self._test_directory_permissions(system_tmp):
            logger.info(f"Using system tmp directory: {system_tmp}")
            return system_tmp

        raise InvokeError("Unable to create or write to temporary directory")

    def _test_directory_permissions(self, directory: str) -> bool:
        """Test directory permissions: create, write, execute, cleanup"""
        try:
            os.makedirs(directory, exist_ok=True)
            test_file = os.path.join(directory, f'.test_{os.getpid()}')

            # Test write permission
            with open(test_file, 'w') as f:
                f.write('test')

            # Test execute permission (important for directories)
            if not os.access(directory, os.X_OK):
                return False

            # Cleanup test file
            os.remove(test_file)
            return True
        except Exception as e:
            logger.debug(f"Directory permission test failed for {directory}: {e}")
            return False

    def __init__(self, plugin_root: str = None):
        # Use plugin root or system tmp with fallback
        from pathlib import Path
        self.plugin_root = plugin_root or os.getcwd()
        self.temp_binaries_dir = Path(self._get_available_temp_directory())
        self.temp_binaries_dir.mkdir(parents=True, exist_ok=True)

    def get_temp_binary_path(self, arch: str, version: str) -> str:
        """Get the version-aware temporary path for a binary architecture."""
        return str(self.temp_binaries_dir / f'echarts-convert-{version}-linux-{arch}')

    def decompress_to_temp(self, compressed_path: str, arch: str, version: str) -> str:
        """
        Decompress binary to version-aware temp location with error handling.
        It reuses the binary if it already exists and is executable.
        """
        temp_binary_path = self.get_temp_binary_path(arch, version)

        # Check if file exists and is executable
        if os.path.exists(temp_binary_path) and os.access(temp_binary_path, os.X_OK):
            # Update access time to avoid cache cleanup
            os.utime(temp_binary_path, None)
            return temp_binary_path

        try:
            # Ensure cache directory exists
            self.temp_binaries_dir.mkdir(parents=True, exist_ok=True)

            if not os.path.exists(compressed_path):
                raise InvokeError(f"Compressed binary not found: {compressed_path}")

            if not os.access(compressed_path, os.R_OK):
                raise InvokeError(f"Compressed binary not readable: {compressed_path}")

            import gzip
            try:
                with gzip.open(compressed_path, 'rb') as compressed_file:
                    with open(temp_binary_path, 'wb') as temp_file:
                        shutil.copyfileobj(compressed_file, temp_file)
            except gzip.BadGzipFile as e:
                raise InvokeError(f"Invalid gzip file: {compressed_path}. Error: {e}")
            except Exception as e:
                raise InvokeError(f"Failed to decompress {compressed_path}: {e}")

            try:
                os.chmod(temp_binary_path, 0o755)
            except OSError as e:
                raise InvokeError(f"Failed to set executable permissions on {temp_binary_path}: {e}")

            if not os.access(temp_binary_path, os.X_OK):
                raise InvokeError(f"Decompressed binary is not executable: {temp_binary_path}")

            logger.info(f"Successfully decompressed {compressed_path} to {temp_binary_path}")
            return temp_binary_path

        except InvokeError:
            raise
        except OSError as e:
            raise InvokeError(f"File system error during decompression to {temp_binary_path}: {e}")
        except Exception as e:
            raise InvokeError(f"Unexpected error during binary decompression for {compressed_path}: {e}")

    def get_binary_path(self, bin_dir: str, arch: str, plugin_root: str) -> Optional[str]:
        """Get binary file path with versioned file management support"""
        try:
            # Read current plugin version
            current_version = get_plugin_version(plugin_root)
            logger.debug(f"Current plugin version: {current_version}")

            # Select appropriate binary version and clean up old versions
            selected_version = select_binary_version(bin_dir, current_version)

            # Build compressed file path
            compressed_binary_path = os.path.join(bin_dir, f'echarts-convert-{selected_version}-linux-{arch}.gz')

            if not os.path.exists(compressed_binary_path):
                raise FileNotFoundError(f"Compressed binary not found: {compressed_binary_path}")

            # Decompress to version-aware temporary location
            return self.decompress_to_temp(compressed_binary_path, arch, selected_version)

        except Exception as e:
            raise InvokeError(f"Failed to prepare binary for {arch}: {e}")

    @staticmethod
    def ensure_binaries_available(bin_dir: str, force_binary: bool = True) -> None:
        """Validate that compressed binaries are available for decompression."""
        if not os.path.exists(bin_dir):
            if force_binary:
                raise InvokeError(f"Executables directory does not exist: {bin_dir}")
            return

        compressed_files = [f for f in os.listdir(bin_dir) if f.endswith('.gz')]
        if not compressed_files and force_binary:
            raise InvokeError(f"No compressed binaries (.gz) found in {bin_dir}")
