# 5_visualizer.py
"""
This module contains the logic for creating all data visualizations.
It's separated from the GUI to keep the plotting code clean and reusable.
It uses matplotlib, seaborn, and wordcloud to generate various plots.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from queue import Queue
from typing import Dict, Any
import os

# Import from other project modules
from config import PLOT_STYLE, PLOT_DPI, PLOT_PALETTE
from utils import read_csv_robustly

class Visualizer:
    """
    Handles the creation of plots and visualizations from the analyzed data.
    """

    def __init__(self, queue: Queue):
        """
        Initializes the Visualizer.

        Args:
            queue (Queue): The queue for communicating with the main GUI thread.
        """
        self.queue = queue
        self.df = None

    def load_data(self, filepath: str) -> bool:
        """
        Loads and prepares the data for visualization.

        Args:
            filepath (str): Path to the analyzed CSV file.

        Returns:
            bool: True if data was loaded successfully, False otherwise.
        """
        self.df = read_csv_robustly(filepath, self.queue)
        if self.df is None:
            return False
        
        # Attempt to convert object columns to numeric where possible
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                self.df[col] = pd.to_numeric(self.df[col], errors='ignore')
        
        self.queue.put(f"可视化数据已加载，共 {len(self.df)} 行。")
        return True

    def get_column_types(self) -> Dict[str, list]:
        """
        Identifies and returns lists of numerical and categorical column names.

        Returns:
            Dict[str, list]: A dictionary with "numerical" and "categorical" keys.
        """
        if self.df is None:
            return {"numerical": ["无"], "categorical": ["无"]}
        
        numerical_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        return {
            "numerical": ["无"] + numerical_cols,
            "categorical": ["无"] + categorical_cols
        }

    def generate_plot(self, plot_params: Dict[str, Any]):
        """

        Main plotting function that routes to the specific plot generator.
        This should be run in a separate thread.
        """
        try:
            plt.style.use(PLOT_STYLE)
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei'] # 支持中文
            plt.rcParams['axes.unicode_minus'] = False # 正常显示负号

            plot_type = plot_params.get("plot_type")
            
            if plot_type == "散点图 (Scatter Plot)":
                self._create_scatter_plot(plot_params)
            elif plot_type == "箱形图 (Box Plot)":
                self._create_box_plot(plot_params)
            elif plot_type == "分布图 (Histogram)":
                self._create_histogram(plot_params)
            elif plot_type == "条形图 (Bar Chart)":
                self._create_bar_chart(plot_params)
            elif plot_type == "词云 (Word Cloud)":
                self._create_word_cloud(plot_params)
            else:
                self.queue.put(f"错误: 未知的图表类型 '{plot_type}'")

        except Exception as e:
            self.queue.put(f"错误: 生成图表时出错 - {e}")

    def _validate_and_prepare(self, params: Dict[str, Any], required_cols: list) -> pd.DataFrame | None:
        """
        Validates that required columns are selected and prepares the DataFrame by dropping NaNs.
        """
        for col_key in required_cols:
            if params.get(col_key) is None or params.get(col_key) == "无":
                self.queue.put(f"错误: 请为 '{col_key}' 选择一个有效的列。")
                return None

        # Filter out None values from the list of columns to check
        cols_to_check = [params[key] for key in required_cols if params.get(key) and params.get(key) != "无"]
        
        df_plot = self.df.dropna(subset=cols_to_check).copy()
        if df_plot.empty:
            self.queue.put(f"错误: 根据所选列过滤后，没有可用于绘图的数据。")
            return None
        return df_plot

    def _save_and_show_plot(self, title: str):
        """
        Helper function to save the current plot to a file and then display it.
        """
        filename = f"{title.replace(' ', '_').lower()}.png"
        plt.tight_layout()
        plt.savefig(filename, dpi=PLOT_DPI)
        self.queue.put(f"图表已成功保存为 '{filename}'")
        plt.show()
        plt.close()

    def _create_scatter_plot(self, params: Dict[str, Any]):
        df_plot = self._validate_and_prepare(params, ['x', 'y'])
        if df_plot is None: return

        fig, ax = plt.subplots(figsize=(12, 8))
        sns.scatterplot(
            data=df_plot,
            x=params['x'], y=params['y'],
            hue=params.get('hue') if params.get('hue') != '无' else None,
            size=params.get('size') if params.get('size') != '无' else None,
            sizes=(50, 250),
            alpha=0.7,
            palette=PLOT_PALETTE,
            ax=ax
        )
        title = f"散点图: {params['y']} vs. {params['x']}"
        ax.set_title(title, fontsize=18)
        ax.set_xlabel(params['x'], fontsize=12)
        ax.set_ylabel(params['y'], fontsize=12)
        self._save_and_show_plot(title)

    def _create_box_plot(self, params: Dict[str, Any]):
        df_plot = self._validate_and_prepare(params, ['x', 'y'])
        if df_plot is None: return

        fig, ax = plt.subplots(figsize=(14, 8))
        sns.boxplot(
            data=df_plot,
            x=params['x'], y=params['y'],
            hue=params.get('hue') if params.get('hue') != '无' else None,
            palette=PLOT_PALETTE,
            ax=ax
        )
        plt.xticks(rotation=45, ha='right')
        title = f"箱形图: {params['y']} by {params['x']}"
        ax.set_title(title, fontsize=18)
        ax.set_xlabel(params['x'], fontsize=12)
        ax.set_ylabel(params['y'], fontsize=12)
        self._save_and_show_plot(title)

    def _create_histogram(self, params: Dict[str, Any]):
        df_plot = self._validate_and_prepare(params, ['x'])
        if df_plot is None: return

        fig, ax = plt.subplots(figsize=(12, 7))
        sns.histplot(
            data=df_plot,
            x=params['x'],
            kde=True,
            hue=params.get('hue') if params.get('hue') != '无' else None,
            palette=PLOT_PALETTE,
            ax=ax
        )
        title = f"分布图: {params['x']}"
        ax.set_title(title, fontsize=18)
        ax.set_xlabel(params['x'], fontsize=12)
        ax.set_ylabel("频数", fontsize=12)
        self._save_and_show_plot(title)

    def _create_bar_chart(self, params: Dict[str, Any]):
        df_plot = self._validate_and_prepare(params, ['x'])
        if df_plot is None: return
        
        # For bar chart, we typically count frequencies of a categorical variable
        if df_plot[params['x']].dtype == 'object' or isinstance(df_plot[params['x']].dtype, pd.CategoricalDtype):
            counts = df_plot[params['x']].value_counts().nlargest(20) # Top 20
            
            fig, ax = plt.subplots(figsize=(14, 8))
            sns.barplot(x=counts.index, y=counts.values, palette=PLOT_PALETTE, ax=ax)
            plt.xticks(rotation=45, ha='right')
            
            title = f"条形图: {params['x']} 的频数统计"
            ax.set_title(title, fontsize=18)
            ax.set_xlabel(params['x'], fontsize=12)
            ax.set_ylabel("计数", fontsize=12)
            self._save_and_show_plot(title)
        else:
            self.queue.put("错误: 条形图仅适用于分类数据列。")

    def _create_word_cloud(self, params: Dict[str, Any]):
        df_plot = self._validate_and_prepare(params, ['x'])
        if df_plot is None: return
        
        text_column = params['x']
        if df_plot[text_column].dtype != 'object':
            self.queue.put(f"错误: 词云只能从文本（分类）列生成。")
            return
            
        text_data = " ".join(str(v) for v in df_plot[text_column].dropna())
        
        if not text_data.strip():
            self.queue.put(f"错误: 列 '{text_column}' 中没有可用于生成词云的文本数据。")
            return
            
        try:
            wordcloud = WordCloud(
                width=1200, height=800,
                background_color='white',
                font_path='msyh.ttc',  # 指定一个支持中文的字体文件路径
                colormap=PLOT_PALETTE,
                max_words=150,
                contour_width=3,
                contour_color='steelblue'
            ).generate(text_data)
            
            plt.figure(figsize=(12, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis("off")
            
            title = f"词云: {text_column}"
            plt.title(title, fontsize=18)
            self._save_and_show_plot(title)
        except Exception as e:
            self.queue.put(f"错误: 生成词云失败。请确保已安装 wordcloud 库并指定了正确的中文字体路径。错误: {e}")
