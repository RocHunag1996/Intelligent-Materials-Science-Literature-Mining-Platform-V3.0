# 3_prompt_manager.py
"""
This module is responsible for managing prompt templates.
It automatically discovers, loads, and provides access to prompt files
stored in a dedicated directory, making it easy to add or modify prompts
without changing the application's code.
"""

import os
from typing import Dict, List
from queue import Queue

# Import from other project modules
from config import PROMPTS_DIR

class PromptManager:
    """
    Handles loading and managing prompt templates from the 'prompts' directory.
    """
    def __init__(self, queue: Queue):
        """
        Initializes the PromptManager, finds and loads all available prompts.

        Args:
            queue (Queue): The queue for logging messages to the GUI.
        """
        self.queue = queue
        self.prompts: Dict[str, str] = {}
        self.load_prompts()

    def load_prompts(self) -> None:
        """
        Scans the prompts directory for .txt files and loads them into memory.
        """
        self.prompts = {}
        if not os.path.exists(PROMPTS_DIR):
            self.queue.put(f"警告: 提示词目录 '{PROMPTS_DIR}' 不存在，将创建一个。")
            os.makedirs(PROMPTS_DIR)
            return

        try:
            for filename in os.listdir(PROMPTS_DIR):
                if filename.endswith(".txt"):
                    prompt_name = os.path.splitext(filename)[0].replace("_", " ").title()
                    filepath = os.path.join(PROMPTS_DIR, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            self.prompts[prompt_name] = f.read()
                        self.queue.put(f"成功加载提示词: '{prompt_name}'")
                    except Exception as e:
                        self.queue.put(f"错误: 加载提示词文件 '{filename}' 失败 - {e}")
            
            if not self.prompts:
                self.queue.put(f"警告: 在 '{PROMPTS_DIR}' 目录中未找到任何 .txt 提示词文件。")

        except Exception as e:
            self.queue.put(f"错误: 扫描提示词目录时出错 - {e}")

    def get_prompt_names(self) -> List[str]:
        """
        Returns a list of the names of all loaded prompts.

        Returns:
            List[str]: A list of prompt names.
        """
        return list(self.prompts.keys())

    def get_prompt_template(self, name: str) -> str | None:
        """
        Retrieves the content of a prompt template by its name.

        Args:
            name (str): The name of the prompt to retrieve.

        Returns:
            str | None: The prompt template string, or None if not found.
        """
        return self.prompts.get(name)
