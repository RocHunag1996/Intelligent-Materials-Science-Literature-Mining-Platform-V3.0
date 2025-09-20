# utils.py
"""
This module contains general-purpose utility functions that are used across
different parts of the application. This helps to keep the code DRY (Don't Repeat Yourself).
"""

import pandas as pd
import io
from queue import Queue

def read_csv_robustly(filepath: str, queue: Queue) -> pd.DataFrame | None:
    """
    Reads a CSV file with robust encoding handling (UTF-8 and GBK).
    This is crucial for dealing with files from different operating systems and sources.

    Args:
        filepath (str): The path to the CSV file.
        queue (Queue): The queue for sending log messages to the GUI.

    Returns:
        pd.DataFrame | None: A pandas DataFrame if successful, otherwise None.
    """
    if not filepath:
        queue.put("错误: 文件路径不能为空。")
        return None
    try:
        # First, try to read with UTF-8, which is the most common encoding.
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return pd.read_csv(io.StringIO(content))
    except UnicodeDecodeError:
        # If UTF-8 fails, it might be an older file from a Windows environment.
        queue.put("提示: UTF-8 解码失败，正在尝试使用 GBK 编码...")
        try:
            with open(filepath, 'r', encoding='gbk', errors='replace') as f:
                content = f.read()
            return pd.read_csv(io.StringIO(content))
        except Exception as e:
            queue.put(f"错误: 使用 GBK 编码读取文件时也失败了 - {e}")
            return None
    except FileNotFoundError:
        queue.put(f"错误: 找不到文件 - {filepath}")
        return None
    except Exception as e:
        queue.put(f"错误: 读取文件时发生未知错误 - {e}")
        return None

def flatten_json_result(data: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    Flattens a nested JSON (dict) object into a single-level dictionary.
    This is essential for converting the nested JSON output from LLMs into a flat
    structure that can be easily saved in a CSV row.

    Example:
        Input: {'a': 1, 'b': {'c': 2, 'd': 3}}
        Output: {'a': 1, 'b_c': 2, 'b_d': 3}

    Args:
        data (dict): The dictionary to flatten.
        parent_key (str): The prefix to prepend to keys.
        sep (str): The separator between parent and child keys.

    Returns:
        dict: The flattened dictionary.
    """
    items = {}
    if not isinstance(data, dict):
        return {parent_key or 'value': data}
        
    for k, v in data.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_json_result(v, new_key, sep=sep))
        elif isinstance(v, list):
            # Convert list to a string representation for CSV compatibility
            items[new_key] = ', '.join(map(str, v))
        else:
            items[new_key] = v
    return items
