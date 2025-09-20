# config.py
"""
Configuration file for the Materials Science Literature Miner.
All user-configurable settings and constants are stored here.
This approach centralizes configuration, making the application easier to manage and update.
"""

# --- Concurrency Configuration ---
# Maximum number of worker threads for parallel API requests.
# WARNING: Setting this too high (>15) can overwhelm some API servers or lead to rate limiting.
# A value between 5 and 10 is a safe start.
MAX_WORKERS = 10

# Delay in seconds between submitting each request to the thread pool.
# Helps to prevent overwhelming the API server with a sudden burst of requests.
REQUEST_SUBMISSION_DELAY = 0.1

# Number of times to retry a failed API request. Essential for handling transient network issues.
MAX_RETRIES = 3

# Save results to the output file after processing this many articles.
# This prevents data loss in case of an interruption during a long run.
SAVE_INTERVAL = 100

# Timeout in seconds for each individual API request.
API_REQUEST_TIMEOUT = 120

# --- API Provider Configuration ---
# List of supported Large Language Model providers.
# This list populates the dropdown menu in the GUI.
# Adding a new provider here is the first step to integrating it.
SUPPORTED_API_PROVIDERS = [
    "OpenAI",
    "Anthropic",
    "DeepSeek",
    "Moonshot",
    "Intern-AI (Internal)"
]

# Default API provider to be selected on startup.
DEFAULT_API_PROVIDER = "OpenAI"

# --- API Endpoint and Model Configuration ---
# A centralized dictionary holding credentials, endpoints, and model names for each provider.
# IMPORTANT: It is STRONGLY recommended to use environment variables for API keys
# in a production environment (e.g., os.environ.get("OPENAI_API_KEY", "")).
# For simplicity in this single-file distribution, we allow direct pasting.
API_CONFIGS = {
    "OpenAI": {
        "api_key": "",  # PASTE YOUR OPENAI KEY HERE
        "endpoint": "https://api.openai.com/v1/chat/completions",
        "model_list": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o"
    },
    "Anthropic": {
        "api_key": "",  # PASTE YOUR ANTHROPIC KEY HERE
        "endpoint": "https://api.anthropic.com/v1/messages",
        "model_list": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "default_model": "claude-3-sonnet-20240229"
    },
    "DeepSeek": {
        "api_key": "", # PASTE YOUR DEEPSEEK KEY HERE
        "endpoint": "https://api.deepseek.com/chat/completions",
        "model_list": ["deepseek-chat"],
        "default_model": "deepseek-chat"
    },
    "Moonshot": {
        "api_key": "", # PASTE YOUR MOONSHOT (月之暗面) KEY HERE
        "endpoint": "https://api.moonshot.cn/v1/chat/completions",
        "model_list": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "moonshot-v1-8k"
    },
    "Intern-AI (Internal)": {
        "api_key": "",  # PASTE YOUR INTERN-AI BEARER TOKEN HERE
        "endpoint": "https://chat.intern-ai.org.cn/api/v1/chat/completions",
        "model_list": ["intern-s1"],
        "default_model": "intern-s1"
    }
}

# --- GUI Configuration ---
APP_TITLE = "材料科学文献智能挖掘平台 V3.0"
APP_GEOMETRY = "1024x768"
FONT_FAMILY = ("Microsoft YaHei UI", 12)

# --- Visualization Configuration ---
# Supported plot types for the visualization tab.
PLOT_TYPES = [
    "散点图 (Scatter Plot)",
    "箱形图 (Box Plot)",
    "分布图 (Histogram)",
    "条形图 (Bar Chart)",
    "词云 (Word Cloud)"
]

# Default plot type.
DEFAULT_PLOT_TYPE = "散点图 (Scatter Plot)"

# Seaborn style for plots. For available styles, see matplotlib documentation.
PLOT_STYLE = "seaborn-v0_8-whitegrid"

# DPI for saved plot images. Higher DPI means higher resolution.
PLOT_DPI = 300

# Color palette for plots. Can be a seaborn palette name (e.g., "viridis", "rocket").
PLOT_PALETTE = "viridis"

# --- Data Processing Configuration ---
# Default columns expected in the input CSV file.
REQUIRED_INPUT_COLUMNS = ["Article Title", "Abstract"]

# --- File Paths ---
# Directory for storing prompt templates.
PROMPTS_DIR = "prompts"

# File name for saving user settings.
SETTINGS_FILE = "app_settings.json"
