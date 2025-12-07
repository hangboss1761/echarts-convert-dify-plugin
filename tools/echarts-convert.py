import json
import logging
import uuid
from collections.abc import Generator
from typing import Any, Dict, Optional

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from .utils import (
    EChartsBlock,
    extract_echarts_blocks,
    replace_blocks_with_images,
    ChartRenderer,
    convert_base64_to_data_url
)

from .utils.logger import get_logger

logger = get_logger(__name__)

class EchartsConvertTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Convert ECharts code blocks in text to images
        """
        try:
            # Get parameters
            content = tool_parameters.get('content', '')
            width = int(tool_parameters.get('width', 800))
            height = int(tool_parameters.get('height', 600))
            concurrency = int(tool_parameters.get('concurrent_rendering', 1))
            merge_echarts_options_str = tool_parameters.get('mergeEchartsOptions', '')

            # Validate parameters
            width = max(100, min(4000, width))
            height = max(100, min(4000, height))
            concurrency = max(0, min(10, concurrency))

            # Parse merge options
            merge_options: Optional[Dict[str, Any]] = None
            if merge_echarts_options_str:
                try:
                    merge_options = json.loads(merge_echarts_options_str)
                except json.JSONDecodeError as e:
                    yield self.create_json_message({
                        "success": False,
                        "error": f"Invalid mergeEchartsOptions JSON: {str(e)}",
                        "processed": 0,
                        "successful": 0,
                        "failed": 0
                    })
                    return

            # Extract echarts code blocks
            blocks = extract_echarts_blocks(content)

            if not blocks:
                yield self.create_text_message(content)
                yield self.create_json_message({
                    "success": True,
                    "processed": 0,
                    "successful": 0,
                    "failed": 0,
                    "message": "No echarts code blocks found"
                })
                return

            # Get valid configurations
            valid_configs = [block.config for block in blocks if block.config and not block.error]
            valid_indices = [i for i, block in enumerate(blocks) if block.config and not block.error]

            if not valid_configs:
                yield self.create_text_message(content)
                yield self.create_json_message({
                    "success": False,
                    "processed": len(blocks),
                    "successful": 0,
                    "failed": len(blocks),
                    "message": "No valid echarts configurations"
                })
                return

            # Render charts (SVG only)
            renderer = ChartRenderer()
            render_results = renderer.render_charts(
                configs=valid_configs,
                width=width,
                height=height,
                concurrency=concurrency,
                merge_options=merge_options
            )

            # Process results
            image_urls = [None] * len(blocks)
            blob_messages = []
            successful_count = 0
            failed_count = 0

            for i, (block_index, render_result) in enumerate(zip(valid_indices, render_results)):
                if render_result.success and render_result.data:
                    successful_count += 1
                    image_url = convert_base64_to_data_url(render_result.data, render_result.mime_type)
                    image_urls[block_index] = image_url

                    # Create blob message for the raw image data
                    blob_messages.append(self.create_blob_message(
                        blob=render_result.data,
                        meta={'mime_type': render_result.mime_type}
                    ))

                else:
                    failed_count += 1
                    logger.error(f"Failed to render block {block_index}: {render_result.error}")

            # Replace successful blocks with image placeholders that won't be escaped
            final_urls = []
            for i, block in enumerate(blocks):
                if image_urls[i]:
                    final_urls.append(image_urls[i])
                else:
                    final_urls.append(block.raw)

            updated_content = replace_blocks_with_images(content, blocks, final_urls)

            # Generate result summary
            result_summary = {
                "success": successful_count > 0,
                "processed": len(blocks),
                "successful": successful_count,
                "failed": failed_count,
                "render_type": "svg",
                "image_type": "svg",
                "concurrency_used": concurrency
            }

            # Yield results - first blob messages, then image messages, then text and summary
            for blob_msg in blob_messages:
                yield blob_msg

            yield self.create_text_message(updated_content)
            yield self.create_json_message(result_summary)

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            yield self.create_json_message({
                "success": False,
                "error": str(e),
                "processed": 0,
                "successful": 0,
                "failed": 0
            })