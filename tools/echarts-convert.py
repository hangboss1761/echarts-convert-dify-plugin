import json
import logging
from collections.abc import Generator
from typing import Any, Dict, Optional, Tuple, List

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.model import InvokeError

from .utils import (
    EChartsBlock,
    extract_echarts_blocks,
    replace_blocks_with_images,
    ChartRenderer,
    convert_base64_to_data_url,
    RenderResult,
)
from .utils.logger import get_logger

logger = get_logger(__name__)

class EchartsConvertTool(Tool):
    """
    A Dify tool to convert ECharts JSON configurations within text into images.
    """

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        """
        Coordinates the entire process of converting ECharts blocks to images.
        It delegates tasks to private methods for clarity and maintainability.
        """
        try:
            is_ready, context = self._prepare_and_validate(tool_parameters)
            if not is_ready:
                yield from context  # Yields early-exit messages
                return

            processed_results = self._render_and_process(context)
            yield from self._build_and_yield_response(context, processed_results)

        except InvokeError as e:
            logger.error(f"A known plugin error occurred: {e}")
            yield self.create_json_message({"success": False, "error": str(e)})
        except Exception as e:
            logger.error(f"An unexpected tool execution error occurred: {e}", exc_info=True)
            yield self.create_json_message({"success": False, "error": f"An unexpected error occurred: {e}"})

    def _prepare_and_validate(self, tool_parameters: dict[str, Any]) -> Tuple[bool, Any]:
        """
        Parses and validates tool parameters, extracts ECharts blocks,
        and performs pre-checks for rendering.
        """
        # 1. Parse and validate parameters
        # Security: Validate dimensions to prevent DoS attacks
        MIN_DIMENSION = 1
        MAX_DIMENSION = 2000

        try:
            width = int(tool_parameters.get('width', 800))
            if width < MIN_DIMENSION or width > MAX_DIMENSION:
                raise InvokeError(f"Width must be between {MIN_DIMENSION} and {MAX_DIMENSION}, got {width}")
        except (ValueError, TypeError):
            raise InvokeError(f"Width must be an integer between {MIN_DIMENSION} and {MAX_DIMENSION}")

        try:
            height = int(tool_parameters.get('height', 600))
            if height < MIN_DIMENSION or height > MAX_DIMENSION:
                raise InvokeError(f"Height must be between {MIN_DIMENSION} and {MAX_DIMENSION}, got {height}")
        except (ValueError, TypeError):
            raise InvokeError(f"Height must be an integer between {MIN_DIMENSION} and {MAX_DIMENSION}")

        params = {
            'content': tool_parameters.get('content', ''),
            'width': width,
            'height': height,
            'concurrency': max(1, min(4, int(tool_parameters.get('concurrent_rendering', 1)))),
        }
        try:
            merge_opts_str = tool_parameters.get('mergeEchartsOptions', '')
            params['merge_options'] = json.loads(merge_opts_str) if merge_opts_str else None
        except json.JSONDecodeError as e:
            raise InvokeError(f"Invalid 'mergeEchartsOptions' JSON: {e}")

        # 2. Extract blocks
        blocks = extract_echarts_blocks(params['content'])
        if not blocks:
            return False, [
                self.create_text_message(params['content']),
                self.create_json_message({"success": True, "message": "No ECharts code blocks found."})
            ]

        # 3. Filter for valid blocks
        valid_items = [(i, b) for i, b in enumerate(blocks) if b.config and not b.error]
        if not valid_items:
            return False, [
                self.create_text_message(params['content']),
                self.create_json_message({"success": False, "message": "No valid ECharts configurations found."})
            ]

        context = {
            "params": params,
            "blocks": blocks,
            "valid_indices": [i for i, b in valid_items],
            "valid_configs": [b.config for i, b in valid_items],
        }
        return True, context

    def _render_and_process(self, context: dict) -> dict:
        """
        Initializes the renderer, renders the charts, and processes the results.
        """
        params = context['params']

        # 1. Render charts
        renderer = ChartRenderer(force_binary=True)
        render_results = renderer.render_charts(
            configs=context['valid_configs'],
            width=params['width'],
            height=params['height'],
            concurrency=params['concurrency'],
            merge_options=params['merge_options']
        )

        # 2. Process results
        image_urls = [None] * len(context['blocks'])
        blob_messages = []
        successful_count = 0
        failed_details = []

        for i, render_result in enumerate(render_results):
            block_index = context['valid_indices'][i]
            if render_result.success and render_result.data:
                successful_count += 1
                image_url = convert_base64_to_data_url(render_result.data, render_result.mime_type)
                image_urls[block_index] = image_url
                blob_messages.append(self.create_blob_message(
                    blob=render_result.data,
                    meta={'mime_type': render_result.mime_type}
                ))
            else:
                error_info = {
                    'block_index': block_index,
                    'error': render_result.error or 'Unknown error'
                }
                failed_details.append(error_info)
                logger.warning(f"Failed to render block {block_index}: {render_result.error}")

        return {
            "image_urls": image_urls,
            "blob_messages": blob_messages,
            "successful_count": successful_count,
            "failed_count": len(context['valid_configs']) - successful_count,
            "failed_details": failed_details,
            "renderer": renderer,
        }

    def _build_and_yield_response(self, context: dict, processed_results: dict) -> Generator[ToolInvokeMessage, None, None]:
        """
        Builds the final text content and summary, then yields all messages.
        """
        content = context['params']['content']
        blocks = context['blocks']
        image_urls = processed_results['image_urls']

        # 1. Create final text with images embedded
        updated_content = replace_blocks_with_images(content, blocks, image_urls)

        # 2. Build summary
        summary = {
            "success": processed_results['successful_count'] > 0,
            "processed": len(blocks),
            "successful": processed_results['successful_count'],
            "failed": processed_results['failed_count'],
            "failed_details": processed_results.get('failed_details', []),  # 包含失败详情
            "render_type": "svg",
            "image_type": "svg",
            "concurrency_used": context['params']['concurrency'],
            # "system": processed_results['renderer'].get_system_info_for_json()  # 注释掉系统信息，生产环境不需要暴露
        }

        # 3. Yield all messages in order
        yield from processed_results['blob_messages']
        yield self.create_text_message(updated_content)
        yield self.create_json_message(summary)

