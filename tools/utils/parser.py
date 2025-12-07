import re
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class EChartsBlock:
    """Represents an ECharts code block"""
    raw: str              # Raw code block text (including ```echarts ... ```)
    config: Optional[Dict[str, Any]]  # Parsed JSON configuration
    start_pos: int        # Start position in original text
    end_pos: int          # End position in original text
    error: Optional[str] = None  # Error message if JSON parsing failed

def extract_echarts_blocks(content: str) -> List[EChartsBlock]:
    """
    Extract all echarts code blocks from text

    Args:
        content: Text content that may contain ```echarts``` code blocks

    Returns:
        List of EChartsBlock objects
    """
    blocks = []

    # Regular expression to match ```echarts ... ``` code blocks
    pattern = r'```echarts\s*\n(.*?)\n```'
    matches = list(re.finditer(pattern, content, re.DOTALL | re.IGNORECASE))

    for match in matches:
        raw_code = match.group(0)
        json_content = match.group(1).strip()

        try:
            config = json.loads(json_content)
            blocks.append(EChartsBlock(
                raw=raw_code,
                config=config,
                start_pos=match.start(),
                end_pos=match.end(),
                error=None
            ))
        except json.JSONDecodeError as e:
            blocks.append(EChartsBlock(
                raw=raw_code,
                config=None,
                start_pos=match.start(),
                end_pos=match.end(),
                error=f"Invalid JSON: {str(e)}"
            ))

    return blocks

def replace_blocks_with_images(
    content: str,
    blocks: List[EChartsBlock],
    image_urls: List[str]
) -> str:
    """
    Replace echarts code blocks with markdown image syntax

    Args:
        content: Original text content
        blocks: List of EChartsBlock objects
        image_urls: List of image URLs corresponding to each block

    Returns:
        Modified text with echarts blocks replaced by images
    """
    if len(blocks) != len(image_urls):
        raise ValueError("Number of blocks and image URLs must match")

    # Start from the end to avoid position changes
    result = content
    for block, image_url in zip(reversed(blocks), reversed(image_urls)):
        if block.error or not image_url:
            # Keep original block if there was an error
            continue

        # Generate markdown image syntax with index
        block_index = len(blocks) - blocks.index(block)
        image_markdown = f"![]({image_url})"

        # Replace the block with image markdown
        result = result[:block.start_pos] + image_markdown + result[block.end_pos:]

    return result