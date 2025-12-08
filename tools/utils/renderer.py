import subprocess
import json
import base64
import os
import platform
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from dify_plugin.errors.model import InvokeError
from .logger import get_logger
from .binary_manager import BinaryManager

logger = get_logger(__name__)

@dataclass
class RenderResult:
    """Represents the result of chart rendering."""
    success: bool
    data: Optional[bytes] = None
    mime_type: Optional[str] = None
    error: Optional[str] = None
    index: Optional[int] = None


class ChartRenderer:
    """Chart renderer that uses a native binary or a JavaScript runtime."""

    def __init__(self, js_executor_path: str = None, force_binary: bool = True):
        """Initializes the renderer by selecting the best available execution method."""
        self.force_binary = force_binary
        self.plugin_root = os.getcwd()

        self.js_executor_path = js_executor_path or os.path.join(self.plugin_root, 'js-executor')
        self.js_executor_script = os.path.join(self.js_executor_path, 'index.ts')

        # Initialize version-aware binary manager
        self.binary_manager = BinaryManager(plugin_root=self.plugin_root)

        self.system_info = self._get_system_info()
        self.binary_path = self._select_executor()
        self.system_info['executor_type'] = 'binary' if self.binary_path else 'runtime'

        if self.force_binary:
            self._validate_executor_selection()

        executor_name = os.path.basename(self.binary_path) if self.binary_path else "JavaScript runtime"
        logger.info(f"Using executor: {executor_name}")

    def _select_executor(self) -> Optional[str]:
        """Sequentially tries to find the best available executor."""
        # 1. Check for local debugging executable from environment variable
        local_path_env = os.environ.get('ECHARTS_CONVERT_LOCAL_PATH')
        if local_path_env and os.access(local_path_env, os.X_OK):
            return local_path_env

        # 2. Check for default local debugging executable
        default_local_path = os.path.join(self.plugin_root, 'echarts-convert-local')
        if os.path.isfile(default_local_path) and os.access(default_local_path, os.X_OK):
            return default_local_path

        # 3. On Linux, try to find and decompress the production binary
        if self.system_info['platform'] == 'linux':
            try:
                bin_dir = os.path.join(self.plugin_root, 'executables')
                BinaryManager.ensure_binaries_available(bin_dir, force_binary=self.force_binary)
                arch = self.system_info['normalized_arch']
                return self.binary_manager.get_binary_path(bin_dir, arch, self.plugin_root)
            except InvokeError as e:
                logger.warning(f"Binary deployment failed, falling back to runtime: {e}")
                if self.force_binary:
                    raise e

        # 4. Fallback to JavaScript runtime
        return None

    def _validate_executor_selection(self):
        """Ensures a valid executor is selected in production (force_binary=True) mode."""
        if self.binary_path:
            return

        bin_dir = os.path.join(self.plugin_root, 'executables')
        if not os.path.exists(bin_dir):
            raise InvokeError(f"Binary directory not found: {bin_dir}")

        expected_binary = self.system_info.get('expected_binary', 'echarts-convert-linux-...')
        expected_path = os.path.join(bin_dir, f"{expected_binary}.gz")
        if not os.path.exists(expected_path):
            available = [f for f in os.listdir(bin_dir) if f.endswith('.gz')]
            raise InvokeError(f"Expected binary '{expected_path}' not found. Available: {available}")
        else:
            raise InvokeError(f"Binary for platform {self.system_info['platform']}-{self.system_info['normalized_arch']} not found or not executable.")

    def _build_command(self, width: int, height: int, concurrency: int, merge_options: Optional[Dict]) -> tuple[List[str], Optional[str]]:
        """Builds the subprocess command and determines the working directory."""
        if self.binary_path:
            base_cmd, cwd = [self.binary_path], None
        else:
            base_cmd, cwd = ['bun', 'run', self.js_executor_script], self.js_executor_path

        cmd = base_cmd + [
            '--width', str(width),
            '--height', str(height),
            '--concurrency', str(concurrency)
        ]
        if merge_options:
            cmd.extend(['--merge-options', json.dumps(merge_options, ensure_ascii=False)])

        return cmd, cwd

    def _parse_output(self, stdout: str) -> List[RenderResult]:
        """Parses the JSON output from the executor into RenderResult objects."""
        try:
            output_data = json.loads(stdout)
            results = output_data.get('results', [])
            render_results = []

            for i, item in enumerate(results):
                if item.get('success'):
                    data_url = item.get('data', '')
                    if data_url.startswith('data:image/svg+xml;base64,'):
                        base64_part = data_url.split(',', 1)[1]
                        svg_data = base64.b64decode(base64_part)
                        render_results.append(RenderResult(success=True, data=svg_data, mime_type='image/svg+xml', index=i))
                    else:
                        render_results.append(RenderResult(success=False, error="Invalid SVG output format", index=i))
                else:
                    render_results.append(RenderResult(success=False, error=item.get('error', 'Unknown error'), index=i))

            return render_results
        except json.JSONDecodeError as e:
            raise InvokeError(f"ECharts output parsing failed: Invalid JSON response. Error: {e}")

    def render_charts(
        self,
        configs: List[Dict[str, Any]],
        width: int = 800,
        height: int = 600,
        concurrency: int = 1,
        merge_options: Optional[Dict[str, Any]] = None
    ) -> List[RenderResult]:
        """Batch renders ECharts configurations to SVG images."""
        # Security: Validate dimensions to prevent DoS attacks (defense in depth)
        MIN_DIMENSION = 1
        MAX_DIMENSION = 2000

        if not isinstance(width, int) or width < MIN_DIMENSION or width > MAX_DIMENSION:
            raise InvokeError(f"Width must be an integer between {MIN_DIMENSION} and {MAX_DIMENSION}, got {width}")
        if not isinstance(height, int) or height < MIN_DIMENSION or height > MAX_DIMENSION:
            raise InvokeError(f"Height must be an integer between {MIN_DIMENSION} and {MAX_DIMENSION}, got {height}")

        # Note: Concurrency validation is already done in tools/echarts-convert.py
        # This method assumes concurrency is already in valid range (1-4)
        cmd, cwd = self._build_command(width, height, concurrency, merge_options)
        configs_json = json.dumps(configs, ensure_ascii=False)

        # Security: Limit JSON input size to prevent DoS attacks
        MAX_JSON_INPUT_SIZE = 50 * 1024 * 1024  # 50MB
        json_size = len(configs_json.encode('utf-8'))
        if json_size > MAX_JSON_INPUT_SIZE:
            raise InvokeError(
                f"Input JSON size ({json_size} bytes) exceeds maximum allowed size "
                f"({MAX_JSON_INPUT_SIZE} bytes). Please reduce the number or complexity of charts."
            )

        logger.info(f"Rendering {len(configs)} chart(s)...")

        try:
            result = subprocess.run(
                cmd,
                input=configs_json,
                text=True,
                capture_output=True,
                timeout=360,
                cwd=cwd,
                check=True  # Raises CalledProcessError on non-zero exit codes
            )
            return self._parse_output(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = f"ECharts conversion failed ({self.system_info['executor_type']}): {e.stderr.strip()}"
            raise InvokeError(error_msg)
        except FileNotFoundError:
            raise InvokeError(f"Executor command not found: '{cmd[0]}'. Please ensure it is installed and in the system's PATH.")
        except Exception as e:
            raise InvokeError(f"An unexpected error occurred during chart rendering: {e}")

    def _get_system_info(self) -> Dict[str, Any]:
        """Gets system information for debugging and responses."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        arch_map = {'x86_64': 'x64', 'amd64': 'x64', 'aarch64': 'arm64', 'arm64': 'arm64'}
        arch = arch_map.get(machine, machine)

        try:
            from .version_manager import get_plugin_version, get_versioned_binary_name
            version = get_plugin_version(self.plugin_root)
            expected_binary = get_versioned_binary_name(version, arch)
        except Exception as e:
            logger.warning(f"Failed to read plugin version: {e}")
            expected_binary = f'echarts-convert-linux-{arch}'

        return {
            'platform': system,
            'machine': machine,
            'normalized_arch': arch,
            'expected_binary': expected_binary,
            'force_binary': self.force_binary,
            'executor_type': 'unknown'
        }

    def get_system_info_for_json(self) -> Dict[str, Any]:
        """Gets system information formatted for JSON responses."""
        info = self.system_info.copy()
        info['binary_available'] = bool(self.binary_path)
        if self.binary_path:
            info['binary_name'] = os.path.basename(self.binary_path)
        return info

def convert_base64_to_data_url(data: bytes, mime_type: str) -> str:
    """Converts binary data to a base64 data URL."""
    base64_data = base64.b64encode(data).decode('ascii')
    return f"data:{mime_type};base64,{base64_data}"
