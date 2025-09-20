# Intelligent-Materials-Science-Literature-Mining-Platform-V3.0

# 智能材料科学文献挖掘平台 V3.0

一个强大、可扩展的桌面应用程序，利用大语言模型（LLM）从海量科学文献中自动、结构化地提取关键信息，并提供丰富的可视化分析功能。

 ---

## ✨ 核心功能

  * **多模型支持**：轻松接入并切换多个主流大语言模型API（OpenAI, Anthropic, DeepSeek, Moonshot等）。
  * **通用性与可扩展性**：通过可插拔的提示词模板系统，从最初的“电池材料”扩展到支持“催化材料”、“通用材料”等任意研究领域。
  * **强大的数据挖掘**：
      * 支持高并发API请求，显著提升处理效率。
      * 具备“断点续跑”功能，在任务中断后可从上次的进度继续。
      * 处理过程中定时保存，防止意外情况下的数据丢失。
  * **交互式数据探索**：在进行大规模分析前，可快速加载、预览数据，并查看详细的统计摘要。
  * **丰富的可视化**：内置多种图表类型（散点图、箱形图、分布图、条形图、词云），帮助用户直观地理解和分析挖掘出的数据。
  * **用户友好的设置管理**：自动保存API密钥、文件路径等用户设置，提升日常使用体验。
  * **模块化设计**：项目代码结构清晰，分为GUI、API客户端、数据处理、可视化等多个模块，易于维护和二次开发。

-----

## 🚀 快速开始

### 1\. 环境准备

确保您已安装 Python 3.9 或更高版本。
克隆或下载此项目到您的本地计算机。

### 2\. 创建项目结构

请确保您的项目文件夹结构如下所示：

```
/MaterialScienceMinerV3
├── main_app.py
├── api_clients.py
├── prompt_manager.py
├── data_processor.py
├── visualizer.py
├── settings_manager.py
├── data_explorer.py
├── utils.py
├── config.py
├── requirements.txt
├── README.md               <-- 就是这个文件！
└── prompts/
    ├── general_materials.txt
    ├── battery_materials.txt
    └── catalysis_materials.txt
```

### 3\. 安装依赖

打开您的终端（命令行），进入项目根目录，然后运行以下命令来安装所有必需的Python库：

```bash
pip install -r requirements.txt
```

### 4\. 配置API密钥

1.  首次运行 `1_main_app.py`，程序会自动生成一个 `app_settings.json` 文件。
2.  或者，您可以直接运行程序，在图形界面的 **④ API设置** 选项卡中，填入您从各个大模型服务商获取的API密钥。
3.  点击“保存所有API密钥”按钮。

### 5\. 运行程序

在终端中，确保您位于项目根目录，然后运行：

```bash
python main_app.py
```

-----

## 📖 使用指南

软件的详细使用流程，请参考 **⑤ 帮助/关于** 选项卡内的说明。

-----

## 🔧 如何扩展

本平台被设计为高度可扩展的，您可以轻松地添加新的大模型支持和新的分析任务。

### 添加新的大模型API

1.  **在 `config.py` 中注册**:
      * 在 `SUPPORTED_API_PROVIDERS` 列表中添加新的服务商名字。
      * 在 `API_CONFIGS` 字典中为新的服务商添加配置，包括API密钥、端点URL和模型列表。
2.  **创建新的API客户端**:
      * 在 `api_clients.py` 文件中，仿照 `OpenAIClient` 或 `AnthropicClient`，创建一个新的客户端类，并继承自 `BaseAPIClient`。
      * 实现 `analyze_text` 方法，根据新服务商的API文档来构造请求头（headers）和请求体（data）。
3.  **在工厂函数中注册**:
      * 在 `2_api_clients.py` 文件底部的 `get_api_client` 函数中，将新的服务商名字和您创建的客户端类添加到 `client_map` 字典中。

### 添加新的提示词模板

1.  在 `prompts` 文件夹中，创建一个新的 `.txt` 文件（例如 `polymeric_materials.txt`）。
2.  仿照已有的模板文件，编写您的结构化信息提取指令。

完成！ 重新启动程序，新的提示词模板将自动出现在“选择提示词模板”的下拉菜单中。

-----

## 🏗️ 项目文件结构解析

  * `main_app.py`: **主程序** - 驱动整个应用的GUI界面和事件循环。
  * `api_clients.py`: **API客户端模块** - 包含所有与外部大模型API交互的逻辑。
  * `prompt_manager.py`: **提示词管理器** - 自动发现并加载 `prompts/` 目录下的所有模板。
  * `data_processor.py`: **数据处理器** - 负责后台的数据挖掘任务，包括多线程处理。
  * `visualizer.py`: **可视化模块** - 负责生成所有图表。
  * `settings_manager.py`: **设置管理器** - 负责读写 `app_settings.json` 配置文件。
  * `data_explorer.py`: **数据探索器** - 提供数据预览和统计摘要功能。
  * `utils.py`: **工具函数库** - 存放通用的辅助函数，如健壮的CSV文件读取。
  * `config.py`: **全局配置文件** - 集中存放所有可配置的常量和参数。
  * `requirements.txt`: **依赖列表** - 定义了项目运行所需的所有Python库。

-----

## 📜 许可证

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 授权。
