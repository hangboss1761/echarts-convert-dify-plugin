import subprocess
import json
import base64
import os
import platform
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class RenderResult:
    """Represents the result of chart rendering"""
    success: bool
    data: Optional[bytes] = None      # Image binary data
    mime_type: Optional[str] = None   # image/svg+xml or image/png
    error: Optional[str] = None       # Error message
    index: Optional[int] = None       # Original chart index


class ChartRenderer:
    """Chart renderer that uses js-executor for ECharts conversion"""

    def __init__(self, js_executor_path: str = None):
        """
        Initialize the chart renderer

        Args:
            js_executor_path: Path to js-executor directory
        """
        if js_executor_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            js_executor_path = os.path.join(
                os.path.dirname(os.path.dirname(current_dir)),
                'js-executor'
            )

        self.js_executor_path = js_executor_path
        self.js_executor_script = os.path.join(js_executor_path, 'index.ts')
        self.binary_path = self._get_binary_path()

        # Log the final executor choice
        if self.binary_path:
            if os.environ.get('ECHARTS_CONVERT_LOCAL_PATH'):
                logger.info(f"ChartRenderer initialized with custom ECHARTS_CONVERT_LOCAL_PATH")
                logger.debug(f"Binary path: {self.binary_path}")
            else:
                logger.info(f"ChartRenderer initialized with binary")
                logger.debug(f"Binary path: {self.binary_path}")
        else:
            logger.info(f"ChartRenderer initialized with Bun runtime")
            logger.debug(f"Script path: {self.js_executor_script}")

    def _get_binary_path(self) -> Optional[str]:
        """
        Get the path to the compiled binary for the current platform
        1. Check for local debugging executable (ECHARTS_CONVERT_LOCAL_PATH or echarts-convert-local)
        2. Check for production Linux binary (packaged in plugin)
        3. Fall back to Bun runtime

        Returns:
            Path to binary executable or None if not found
        """
        # 1. Check for local debugging executable first
        local_binary_path = os.environ.get('ECHARTS_CONVERT_LOCAL_PATH')
        if local_binary_path:
            logger.debug(f"ECHARTS_CONVERT_LOCAL_PATH detected: {local_binary_path}")
            if os.path.isfile(local_binary_path) and os.access(local_binary_path, os.X_OK):
                logger.info(f"Using local debugging executable from ECHARTS_CONVERT_LOCAL_PATH")
                return local_binary_path
            else:
                logger.error(f"Local executable from ECHARTS_CONVERT_LOCAL_PATH not found or not executable")

        # Check default local executable name
        plugin_root = os.path.dirname(os.path.dirname(self.js_executor_path))
        default_local_binary = os.path.join(plugin_root, 'echarts-convert-local')
        if os.path.isfile(default_local_binary) and os.access(default_local_binary, os.X_OK):
            logger.info(f"Using default local debugging executable")
            return default_local_binary

        # 2. Check for production Linux binary
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize architecture names
        arch_map = {
            'x86_64': 'x64',
            'amd64': 'x64',
            'aarch64': 'arm64',
            'arm64': 'arm64',
            'armv7l': 'arm64',  # Treat ARM32 as ARM64 for binary selection
        }

        arch = arch_map.get(machine, machine)
        bin_dir = os.path.join(plugin_root, 'bin')
        binary_name = f'echarts-convert-linux-{arch}'
        binary_path = os.path.join(bin_dir, binary_name)

        if os.path.isfile(binary_path) and os.access(binary_path, os.X_OK):
            logger.info(f"Using production Linux binary")
            logger.debug(f"Binary: {os.path.basename(binary_path)} ({system}-{arch})")
            return binary_path

        # 3. No binary found - log appropriate message and return None
        if system == 'linux':
            logger.info(f"Falling back to Bun runtime (no production binary found)")
            logger.debug("Platform: {system}-{arch}")
        else:
            logger.info(f"Falling back to Bun runtime (no binary available for {system}-{arch})")

        return None


    def render_charts(
        self,
        configs: List[Dict[str, Any]],
        width: int = 800,
        height: int = 600,
        concurrency: int = 1,
        merge_options: Optional[Dict[str, Any]] = None
    ) -> List[RenderResult]:
        """
        Batch render ECharts configurations to SVG images

        Args:
            configs: List of ECharts configuration dictionaries
            width: Chart width in pixels
            height: Chart height in pixels
            concurrency: Number of charts to render concurrently (1-4, default 1)
            merge_options: Global ECharts options to merge with each chart

        Returns:
            List of RenderResult objects
        """
        try:
            # Validate and normalize parameters
            if concurrency < 1 or concurrency > 4:
                logger.warning(f"Concurrency {concurrency} out of range (1-4), using 1")
                concurrency = 1

            # Prepare input JSON
            configs_json = json.dumps(configs, ensure_ascii=False)

            # Determine execution method
            if self.binary_path:
                # Use compiled binary
                cmd = [
                    self.binary_path,
                    '--width', str(width),
                    '--height', str(height),
                    '--concurrency', str(concurrency)
                ]
                if merge_options:
                    cmd.extend(['--merge-options', json.dumps(merge_options, ensure_ascii=False)])

                logger.info(f"Executing with compiled binary")
                logger.debug(f"Binary: {self.binary_path}")
                logger.debug(f"Command: {' '.join(cmd)}")
                cwd = None  # Binary can run from any directory
            else:
                # Use Bun runtime
                cmd = [
                    'bun', 'run', self.js_executor_script,
                    '--width', str(width),
                    '--height', str(height),
                    '--concurrency', str(concurrency)
                ]
                if merge_options:
                    cmd.extend(['--merge-options', json.dumps(merge_options, ensure_ascii=False)])

                logger.info(f"Executing with Bun runtime")
                logger.debug(f"Script: {self.js_executor_script}")
                logger.debug(f"Command: {' '.join(cmd)}")
                cwd = self.js_executor_path

            logger.info(f"Rendering {len(configs)} charts with {concurrency} concurrency")

            # Execute rendering
            result = subprocess.run(
                cmd,
                input=configs_json,
                text=True,
                capture_output=True,
                timeout=60,  # 60 second timeout
                cwd=cwd
            )

            if result.returncode != 0:
                execution_method = "compiled binary" if self.binary_path else "Bun runtime"
                error_msg = f"Execution failed ({execution_method}): {result.stderr}"
                logger.error(error_msg)
                return [RenderResult(
                    success=False,
                    error=error_msg,
                    index=i
                ) for i in range(len(configs))]

            # Parse output
            try:
                output_data = json.loads(result.stdout)
                results = output_data.get('results', [])

                # Convert to RenderResult objects (SVG only)
                render_results = []
                for i, result_item in enumerate(results):
                    if result_item.get('success', False):
                        data_url = result_item.get('data', '')
                        if data_url.startswith('data:image/svg+xml;base64,'):
                            # SVG data
                            base64_part = data_url.split(',', 1)[1]
                            svg_data = base64.b64decode(base64_part)
                            render_results.append(RenderResult(
                                success=True,
                                data=svg_data,
                                mime_type='image/svg+xml',
                                index=i
                            ))
                        else:
                            render_results.append(RenderResult(
                                success=False,
                                error="Invalid SVG output format",
                                index=i
                            ))
                    else:
                        render_results.append(RenderResult(
                            success=False,
                            error=result_item.get('error', 'Unknown error'),
                            index=i
                        ))

                return render_results

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse js-executor output: {e}")
                return [RenderResult(
                    success=False,
                    error=f"Output parsing failed: {str(e)}",
                    index=i
                ) for i in range(len(configs))]

        except Exception as e:
            logger.error(f"Unexpected error during rendering: {e}")
            return [RenderResult(
                success=False,
                error=f"Rendering error: {str(e)}",
                index=i
            ) for i in range(len(configs))]


def convert_base64_to_data_url(data: bytes, mime_type: str) -> str:
    """
    Convert binary data to base64 data URL

    Args:
        data: Binary image data
        mime_type: MIME type (image/svg+xml or image/png)

    Returns:
        Data URL string
    """
    base64_data = base64.b64encode(data).decode('ascii')
    return f"data:{mime_type};base64,{base64_data}"