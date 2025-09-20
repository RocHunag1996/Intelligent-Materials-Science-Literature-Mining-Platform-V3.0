# 6_settings_manager.py
"""
This module handles saving and loading user settings to a local file.
This provides persistence for API keys, selected models, and other preferences
between application sessions, improving the user experience.
"""
import json
import os
from queue import Queue
from typing import Dict, Any

# Import from other project modules
from config import SETTINGS_FILE, API_CONFIGS

class SettingsManager:
    """
    Manages loading and saving application settings from/to a JSON file.
    """

    def __init__(self, queue: Queue):
        """
        Initializes the SettingsManager.

        Args:
            queue (Queue): The queue for logging messages to the GUI.
        """
        self.queue = queue
        self.settings_file = SETTINGS_FILE
        self.settings = self._load_defaults()

    def _load_defaults(self) -> Dict[str, Any]:
        """
        Generates a default settings dictionary from the main config file.
        This ensures the application has a valid settings structure to start with.

        Returns:
            Dict[str, Any]: A dictionary containing default settings.
        """
        defaults = {
            "api_keys": {provider: "" for provider in API_CONFIGS},
            "selected_models": {provider: config["default_model"] for provider, config in API_CONFIGS.items()},
            "last_provider": "OpenAI",
            "last_input_file": "",
            "last_output_file": "",
            "last_viz_file": ""
        }
        return defaults

    def load_settings(self) -> None:
        """
        Loads settings from the JSON file. If the file doesn't exist or is invalid,
        it falls back to default settings.
        """
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge loaded settings with defaults to handle new settings in updates
                default_settings = self._load_defaults()
                # Ensure all keys from defaults exist
                for key, value in default_settings.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = value
                    elif isinstance(value, dict):
                         # Ensure nested dictionaries also have all default keys
                        for sub_key, sub_value in value.items():
                            if sub_key not in loaded_settings[key]:
                                loaded_settings[key][sub_key] = sub_value

                self.settings = loaded_settings
                self.queue.put(f"成功加载用户设置: {self.settings_file}")
            except (json.JSONDecodeError, TypeError) as e:
                self.queue.put(f"警告: 无法解析设置文件，将使用默认设置。错误: {e}")
                self.settings = self._load_defaults()
        else:
            self.queue.put("提示: 未找到设置文件，将使用默认设置。")
            self.settings = self._load_defaults()

    def save_settings(self) -> None:
        """
        Saves the current settings dictionary to the JSON file.
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            self.queue.put(f"用户设置已保存: {self.settings_file}")
        except Exception as e:
            self.queue.put(f"错误: 保存设置失败 - {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a setting value by key.

        Args:
            key (str): The setting key to retrieve.
            default (Any, optional): The value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value of the setting.
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Sets a setting value by key.

        Args:
            key (str): The setting key to update.
            value (Any): The new value for the setting.
        """
        self.settings[key] = value

    def get_api_key(self, provider: str) -> str:
        """
        Retrieves the API key for a specific provider.
        """
        return self.settings.get("api_keys", {}).get(provider, "")

    def set_api_key(self, provider: str, key: str) -> None:
        """
        Sets the API key for a specific provider.
        """
        if "api_keys" not in self.settings:
            self.settings["api_keys"] = {}
        self.settings["api_keys"][provider] = key

    def get_selected_model(self, provider: str) -> str:
        """
        Retrieves the selected model for a specific provider.
        """
        return self.settings.get("selected_models", {}).get(provider, "")

    def set_selected_model(self, provider: str, model: str) -> None:
        """
        Sets the selected model for a specific provider.
        """
        if "selected_models" not in self.settings:
            self.settings["selected_models"] = {}
        self.settings["selected_models"][provider] = model
