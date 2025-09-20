# 7_data_explorer.py
"""
This module provides the data exploration component of the application.
It allows users to load a CSV file and view its contents, column information,
and basic statistics directly within the GUI. This is a crucial feature for
data validation and preliminary analysis.
"""

import pandas as pd
from queue import Queue
from typing import Tuple

# Import from other project modules
from utils import read_csv_robustly

class DataExplorer:
    """
    Handles loading, analyzing, and preparing data for display in the Data Explorer tab.
    """
    def __init__(self, queue: Queue):
        """
        Initializes the DataExplorer.

        Args:
            queue (Queue): The queue for logging messages to the GUI.
        """
        self.queue = queue
        self.df: pd.DataFrame | None = None

    def load_data(self, filepath: str) -> bool:
        """
        Loads a CSV file into a pandas DataFrame.

        Args:
            filepath (str): The path to the CSV file.

        Returns:
            bool: True if loading was successful, False otherwise.
        """
        self.df = read_csv_robustly(filepath, self.queue)
        return self.df is not None

    def get_data_preview(self, num_rows: int = 50) -> pd.DataFrame | None:
        """
        Returns the first few rows of the loaded DataFrame.

        Args:
            num_rows (int): The number of rows to return.

        Returns:
            pd.DataFrame | None: The head of the DataFrame or None if no data is loaded.
        """
        if self.df is not None:
            return self.df.head(num_rows)
        return None

    def get_data_summary(self) -> Tuple[str, pd.DataFrame | None]:
        """
        Generates a summary of the loaded data, including shape, data types,
        and basic statistics for numerical columns.

        Returns:
            Tuple[str, pd.DataFrame | None]: A tuple containing a text summary
            and a DataFrame of descriptive statistics.
        """
        if self.df is None:
            return "没有加载数据。", None

        # Basic Info
        num_rows, num_cols = self.df.shape
        info_text = f"数据概览:\n"
        info_text += f"--------------------\n"
        info_text += f"总行数: {num_rows}\n"
        info_text += f"总列数: {num_cols}\n\n"

        # Data Types and Non-Null Counts
        info_text += "列信息 (类型和非空值):\n"
        info_text += "--------------------\n"
        
        # Create a string buffer to build the dtypes and non-null info table
        lines = []
        for col in self.df.columns:
            non_null_count = self.df[col].count()
            dtype = self.df[col].dtype
            lines.append(f"- {col:<30} | 类型: {str(dtype):<15} | 非空值: {non_null_count}")
        info_text += "\n".join(lines)
        info_text += "\n\n"
        
        # Descriptive Statistics for numerical columns
        numerical_df = self.df.select_dtypes(include=['number'])
        if not numerical_df.empty:
            info_text += "数值列统计摘要:\n"
            info_text += "--------------------\n"
            # Return the description DataFrame to be displayed in a table
            return info_text, numerical_df.describe().round(2)
        else:
            info_text += "数据集中没有数值列可供统计。"
            return info_text, None
