# 1_main_app.py
"""
Main application file for the Materials Science Literature Miner.
This file brings all the components together:
- Creates the main GUI window using customtkinter.
- Manages user interactions and application state.
- Initializes and coordinates the other modules (API clients, data processor, etc.).
- Handles threading to ensure the GUI remains responsive during long operations.
"""

import tkinter
import tkinter.filedialog
from tkinter import messagebox
import customtkinter as ctk
import threading
from queue import Queue
import webbrowser

# --- Import project modules ---
# This modular approach makes the project scalable and easier to maintain.
from config import *
from utils import *
from api_clients import get_api_client
from prompt_manager import PromptManager
from data_processor import DataProcessor
from visualizer import Visualizer
from settings_manager import SettingsManager
from data_explorer import DataExplorer


class LiteratureMinerApp(ctk.CTk):
    """
    The main application class that encapsulates the entire GUI and its functionality.
    """
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # --- Initialize Core Components ---
        self.queue = Queue() # For thread-safe communication with the GUI
        self.settings_manager = SettingsManager(self.queue)
        self.prompt_manager = PromptManager(self.queue)
        self.data_processor = DataProcessor(self.queue)
        self.visualizer = Visualizer(self.queue)
        self.data_explorer = DataExplorer(self.queue)

        # --- Load settings ---
        self.settings_manager.load_settings()

        # --- Main UI Structure ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        self._create_widgets()

        # --- Start the queue processor ---
        self.after(100, self._process_queue)

        # --- Handle window closing ---
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """
        Handles the application closing event, ensuring settings are saved.
        """
        self.log("正在保存用户设置...")
        self.settings_manager.save_settings()
        self.log("设置已保存。再见！")
        self.destroy()

    def _create_widgets(self):
        """
        Creates all the UI components (tabs, buttons, entries, etc.).
        """
        # --- Create the main tab view ---
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.pack(padx=10, pady=10, fill="both", expand=True)

        self.tab_mine = self.tab_view.add("① 数据挖掘")
        self.tab_explore = self.tab_view.add("② 数据探索")
        self.tab_viz = self.tab_view.add("③ 数据可视化")
        self.tab_settings = self.tab_view.add("④ API设置")
        self.tab_help = self.tab_view.add("⑤ 帮助/关于")

        # --- Populate each tab ---
        self._create_mining_tab(self.tab_mine)
        self._create_explorer_tab(self.tab_explore)
        self._create_visualization_tab(self.tab_viz)
        self._create_settings_tab(self.tab_settings)
        self._create_help_tab(self.tab_help)

        # --- Create the bottom status bar and log area ---
        status_frame = ctk.CTkFrame(self.main_frame)
        status_frame.pack(padx=15, pady=10, fill="x")
        status_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(status_frame, orientation="horizontal")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")
        
        self.progress_label = ctk.CTkLabel(status_frame, text="0/0", font=FONT_FAMILY)
        self.progress_label.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.stop_button = ctk.CTkButton(status_frame, text="中止任务", command=self.data_processor.stop, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=10, pady=10)
        
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(padx=15, pady=10, fill="both", expand=True)
        ctk.CTkLabel(log_frame, text="运行日志:", font=FONT_FAMILY).pack(anchor="w", pady=5)
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word", font=FONT_FAMILY)
        self.log_textbox.pack(fill="both", expand=True)

    # --- Tab Creation Methods ---

    def _create_mining_tab(self, tab):
        """Creates the widgets for the 'Data Mining' tab."""
        # --- API and Prompt Selection ---
        api_prompt_frame = ctk.CTkFrame(tab)
        api_prompt_frame.pack(padx=15, pady=10, fill="x")
        api_prompt_frame.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(api_prompt_frame, text="选择大模型:", font=FONT_FAMILY).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.provider_var = ctk.StringVar(value=self.settings_manager.get("last_provider", DEFAULT_API_PROVIDER))
        self.provider_menu = ctk.CTkOptionMenu(api_prompt_frame, variable=self.provider_var, 
                                               values=SUPPORTED_API_PROVIDERS, command=self._on_provider_change,
                                               font=FONT_FAMILY)
        self.provider_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(api_prompt_frame, text="选择模型:", font=FONT_FAMILY).grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.model_var = ctk.StringVar(value="")
        self.model_menu = ctk.CTkOptionMenu(api_prompt_frame, variable=self.model_var, values=[""], font=FONT_FAMILY)
        self.model_menu.grid(row=0, column=3, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(api_prompt_frame, text="选择提示词模板:", font=FONT_FAMILY).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        prompt_names = self.prompt_manager.get_prompt_names()
        self.prompt_var = ctk.StringVar(value=prompt_names[0] if prompt_names else "")
        self.prompt_menu = ctk.CTkOptionMenu(api_prompt_frame, variable=self.prompt_var, values=prompt_names, 
                                             command=self._on_prompt_change, font=FONT_FAMILY)
        self.prompt_menu.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

        # --- File Paths ---
        file_frame = ctk.CTkFrame(tab)
        file_frame.pack(padx=15, pady=5, fill="x")
        
        ctk.CTkLabel(file_frame, text="输入文件 (CSV):", font=FONT_FAMILY).pack(anchor="w")
        self.input_entry = ctk.CTkEntry(file_frame, placeholder_text="选择包含文献数据的 CSV 文件", font=FONT_FAMILY)
        self.input_entry.insert(0, self.settings_manager.get("last_input_file", ""))
        self.input_entry.pack(side="left", fill="x", expand=True, pady=(0,5))
        ctk.CTkButton(file_frame, text="选择...", width=80, command=lambda: self._select_file(self.input_entry, "last_input_file"), font=FONT_FAMILY).pack(side="left", padx=(10,0), pady=(0,5))
        
        ctk.CTkLabel(file_frame, text="输出文件 (CSV):", font=FONT_FAMILY).pack(anchor="w", pady=(5,0))
        self.output_entry = ctk.CTkEntry(file_frame, placeholder_text="选择保存挖掘数据的位置", font=FONT_FAMILY)
        self.output_entry.insert(0, self.settings_manager.get("last_output_file", ""))
        self.output_entry.pack(side="left", fill="x", expand=True, pady=(0,5))
        ctk.CTkButton(file_frame, text="选择...", width=80, command=lambda: self._select_save_file(self.output_entry, "last_output_file"), font=FONT_FAMILY).pack(side="left", padx=(10,0), pady=(0,5))

        # --- Prompt Editor ---
        prompt_frame = ctk.CTkFrame(tab)
        prompt_frame.pack(padx=15, pady=5, fill="both", expand=True)
        ctk.CTkLabel(prompt_frame, text="提示词编辑器:", font=FONT_FAMILY).pack(anchor="w")
        self.prompt_textbox = ctk.CTkTextbox(prompt_frame, height=200, wrap="word", font=FONT_FAMILY)
        self.prompt_textbox.pack(fill="both", expand=True, pady=(0,5))
        
        # --- Control Panel ---
        control_frame = ctk.CTkFrame(tab)
        control_frame.pack(padx=15, pady=5, fill="x")

        ctk.CTkLabel(control_frame, text="处理数量:", font=FONT_FAMILY).pack(side="left", padx=(0,5))
        self.process_count_entry = ctk.CTkEntry(control_frame, width=80, font=FONT_FAMILY)
        self.process_count_entry.insert(0, "0")
        self.process_count_entry.pack(side="left")
        ctk.CTkLabel(control_frame, text="(0 表示全部)", font=FONT_FAMILY).pack(side="left", padx=5)
        
        self.resume_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(control_frame, text="断点续跑模式", variable=self.resume_var, font=FONT_FAMILY).pack(side="left", padx=20)
        
        self.analysis_button = ctk.CTkButton(control_frame, text="开始挖掘", font=(FONT_FAMILY[0], 16), command=self._start_analysis_thread)
        self.analysis_button.pack(side="right", padx=10, pady=10)
        
        # Initial population of menus and text
        self._on_provider_change(self.provider_var.get())
        self._on_prompt_change(self.prompt_var.get())

    def _create_explorer_tab(self, tab):
        """Creates the widgets for the 'Data Explorer' tab."""
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # --- File Selection Frame ---
        file_frame = ctk.CTkFrame(tab)
        file_frame.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        self.explorer_entry = ctk.CTkEntry(file_frame, placeholder_text="选择一个 CSV 文件进行探索...", font=FONT_FAMILY)
        self.explorer_entry.grid(row=0, column=0, padx=(0,10), pady=10, sticky="ew")
        
        ctk.CTkButton(file_frame, text="加载数据", command=self._load_explorer_data, font=FONT_FAMILY).grid(row=0, column=1, pady=10, padx=10)

        # --- Tab View for Preview and Summary ---
        explorer_tab_view = ctk.CTkTabview(tab)
        explorer_tab_view.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")
        
        tab_preview = explorer_tab_view.add("数据预览")
        tab_summary = explorer_tab_view.add("统计摘要")
        
        # --- Data Preview Tab ---
        tab_preview.grid_columnconfigure(0, weight=1)
        tab_preview.grid_rowconfigure(0, weight=1)
        self.explorer_preview_text = ctk.CTkTextbox(tab_preview, state="disabled", wrap="none", font=("Courier New", 11))
        self.explorer_preview_text.grid(row=0, column=0, sticky="nsew")

        # --- Data Summary Tab ---
        tab_summary.grid_columnconfigure(0, weight=1)
        tab_summary.grid_rowconfigure(0, weight=1)
        self.explorer_summary_text = ctk.CTkTextbox(tab_summary, state="disabled", wrap="word", font=FONT_FAMILY)
        self.explorer_summary_text.grid(row=0, column=0, sticky="nsew")

    def _create_visualization_tab(self, tab):
        """Creates the widgets for the 'Data Visualization' tab."""
        # --- File Selection ---
        file_frame = ctk.CTkFrame(tab)
        file_frame.pack(padx=15, pady=10, fill="x")
        self.viz_input_entry = ctk.CTkEntry(file_frame, placeholder_text="选择包含已挖掘数据的 CSV 文件", font=FONT_FAMILY)
        self.viz_input_entry.insert(0, self.settings_manager.get("last_viz_file", ""))
        self.viz_input_entry.pack(side="left", fill="x", expand=True, pady=5)
        ctk.CTkButton(file_frame, text="加载并分析数据", width=120, command=self._load_viz_data, font=FONT_FAMILY).pack(side="left", padx=(10,0), pady=5)

        # --- Custom Plot Frame ---
        plot_frame = ctk.CTkFrame(tab)
        plot_frame.pack(padx=15, pady=10, fill="x")
        plot_frame.grid_columnconfigure((1, 3), weight=1)
        
        ctk.CTkLabel(plot_frame, text="图表类型:", font=FONT_FAMILY).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.plot_type_var = ctk.StringVar(value=DEFAULT_PLOT_TYPE)
        self.plot_type_menu = ctk.CTkOptionMenu(plot_frame, variable=self.plot_type_var, values=PLOT_TYPES, command=self._on_plot_type_change, font=FONT_FAMILY)
        self.plot_type_menu.grid(row=0, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

        # --- Axis and Aesthetic Mappings ---
        self.plot_option_menus = {}
        self.plot_option_vars = {}
        
        options_map = {
            "x_axis": ("X轴:", 1, 0, "ew", ["无"]),
            "y_axis": ("Y轴:", 1, 2, "ew", ["无"]),
            "hue": ("颜色 (Hue):", 2, 0, "ew", ["无"]),
            "size": ("大小 (Size):", 2, 2, "ew", ["无"])
        }

        for name, (label, row, col, sticky, values) in options_map.items():
            ctk.CTkLabel(plot_frame, text=label, font=FONT_FAMILY).grid(row=row, column=col, padx=10, pady=5, sticky="w")
            var = ctk.StringVar(value="无")
            menu = ctk.CTkOptionMenu(plot_frame, variable=var, values=values, font=FONT_FAMILY)
            menu.grid(row=row, column=col+1, padx=10, pady=5, sticky=sticky)
            self.plot_option_vars[name] = var
            self.plot_option_menus[name] = menu
            
        # --- Generate Button ---
        self.plot_button = ctk.CTkButton(tab, text="生成图表", font=(FONT_FAMILY[0], 16), command=self._start_plot_thread)
        self.plot_button.pack(pady=15, padx=20, fill="x")
        self._on_plot_type_change(DEFAULT_PLOT_TYPE) # Initial setup of axis options

    def _create_settings_tab(self, tab):
        """Creates the widgets for the 'API Settings' tab."""
        tab.grid_columnconfigure(0, weight=1)
        
        self.api_key_entries = {}
        
        for i, provider in enumerate(SUPPORTED_API_PROVIDERS):
            frame = ctk.CTkFrame(tab, border_width=1)
            frame.grid(row=i, column=0, padx=20, pady=10, sticky="ew")
            frame.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(frame, text=provider, font=(FONT_FAMILY[0], 14, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            api_key = self.settings_manager.get_api_key(provider)
            entry = ctk.CTkEntry(frame, placeholder_text=f"在此处粘贴您的 {provider} API Key/Token", show="*", font=FONT_FAMILY)
            entry.insert(0, api_key)
            entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            self.api_key_entries[provider] = entry

        save_button = ctk.CTkButton(tab, text="保存所有API密钥", command=self._save_api_keys, font=FONT_FAMILY)
        save_button.grid(row=len(SUPPORTED_API_PROVIDERS), column=0, padx=20, pady=20)

    def _create_help_tab(self, tab):
        """Creates the widgets for the 'Help/About' tab."""
        tab.grid_columnconfigure(0, weight=1)
        
        textbox = ctk.CTkTextbox(tab, wrap="word", font=FONT_FAMILY)
        textbox.pack(padx=20, pady=20, fill="both", expand=True)

        help_text = f"""
        ## {APP_TITLE}

        **欢迎使用材料科学文献智能挖掘平台！**

        这是一个利用大语言模型（LLM）技术，从海量科学文献中自动、结构化地提取关键信息的强大工具。

        ---
        ### **使用流程**

        **1. API设置 (④)**
        - 前往“API设置”选项卡。
        - 在对应输入框中，粘贴您从各服务商（如OpenAI, Anthropic等）获取的API密钥。
        - 点击“保存所有API密钥”。此操作只需在首次使用或更换密钥时进行。

        **2. 数据挖掘 (①)**
        - **选择大模型**: 从下拉菜单中选择您想使用的API服务商和具体模型。
        - **选择提示词模板**: 根据您的研究领域（如“电池材料”或“通用材料”）选择一个模板。您也可以在下方的编辑器中直接修改，或在`prompts`文件夹中创建新的`.txt`模板。
        - **选择输入/输出文件**:
            - **输入文件**: 一个CSV文件，必须包含名为 `Article Title` 和 `Abstract` 的列。
            - **输出文件**: 分析结果将追加保存到此文件。
        - **设置参数**:
            - **处理数量**: 设为0则处理输入文件中的所有文章。
            - **断点续跑**: 勾选后，程序会跳过输出文件中已存在的记录，适合在任务中断后继续。
        - **开始挖掘**: 点击按钮，程序将在后台开始处理。您可以在日志区查看进度。

        **3. 数据探索 (②)**
        - 点击“加载数据”选择一个CSV文件（通常是您挖掘后的输出文件）。
        - **数据预览**: 查看文件的前50行，快速了解数据结构。
        - **统计摘要**: 查看数据的行数、列数、各列类型以及数值列的基本统计信息（均值、方差等）。

        **4. 数据可视化 (③)**
        - 点击“加载并分析数据”选择您的输出文件。
        - **选择图表类型**: 支持散点图、箱形图、分布图、条形图和词云。
        - **配置轴和参数**: 根据图表类型，从下拉菜单中选择合适的列作为X轴、Y轴、颜色分组等。
        - **生成图表**: 点击按钮，图表将在新窗口中显示，并自动保存为PNG图片到程序根目录。

        ---
        ### **关于**
        - 版本: 3.0
        - 作者: [Your Name/Organization]
        - 技术栈: Python, CustomTkinter, Pandas, Matplotlib, Seaborn
        - 如有疑问或建议，请联系: [Your Contact Email]
        """
        textbox.insert("0.0", help_text)
        textbox.configure(state="disabled")

        link_frame = ctk.CTkFrame(tab, fg_color="transparent")
        link_frame.pack(pady=10)
        ctk.CTkLabel(link_frame, text="项目地址:", font=FONT_FAMILY).pack(side="left")
        link_label = ctk.CTkLabel(link_frame, text="GitHub Repository", text_color="cyan", font=(FONT_FAMILY[0], FONT_FAMILY[1], "underline"), cursor="hand2")
        link_label.pack(side="left", padx=5)
        link_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com"))

    # --- Event Handlers and Logic ---

    def log(self, message):
        """Adds a message to the log textbox in a thread-safe manner."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _select_file(self, entry_widget, settings_key):
        """Opens a file dialog to select an input file."""
        filepath = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if filepath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filepath)
            self.settings_manager.set(settings_key, filepath)
            self.log(f"已选择输入文件: {os.path.basename(filepath)}")

    def _select_save_file(self, entry_widget, settings_key):
        """Opens a file dialog to select a save location."""
        filepath = tkinter.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filepath)
            self.settings_manager.set(settings_key, filepath)
            self.log(f"已选择输出位置: {os.path.basename(filepath)}")

    def _on_provider_change(self, provider):
        """Handles the change event for the API provider dropdown."""
        models = API_CONFIGS.get(provider, {}).get("model_list", [])
        self.model_menu.configure(values=models)
        
        # Try to set the saved model for this provider, otherwise set the default
        saved_model = self.settings_manager.get_selected_model(provider)
        if saved_model in models:
            self.model_var.set(saved_model)
        elif models:
            self.model_var.set(models[0])
        else:
            self.model_var.set("")
        self.settings_manager.set("last_provider", provider)

    def _on_prompt_change(self, prompt_name):
        """Handles the change event for the prompt template dropdown."""
        template = self.prompt_manager.get_prompt_template(prompt_name)
        if template:
            self.prompt_textbox.delete("0.0", "end")
            self.prompt_textbox.insert("0.0", template)
    
    def _on_plot_type_change(self, plot_type):
        """Enables/disables axis selection menus based on the selected plot type."""
        # A map of which options are relevant for each plot type
        relevance = {
            "散点图 (Scatter Plot)": ["x_axis", "y_axis", "hue", "size"],
            "箱形图 (Box Plot)": ["x_axis", "y_axis", "hue"],
            "分布图 (Histogram)": ["x_axis", "hue"],
            "条形图 (Bar Chart)": ["x_axis"],
            "词云 (Word Cloud)": ["x_axis"]
        }
        
        active_options = relevance.get(plot_type, [])
        for name, menu in self.plot_option_menus.items():
            if name in active_options:
                menu.configure(state="normal")
            else:
                menu.configure(state="disabled")
                self.plot_option_vars[name].set("无") # Reset inactive options

    def _save_api_keys(self):
        """Saves all API keys from the settings tab."""
        for provider, entry in self.api_key_entries.items():
            self.settings_manager.set_api_key(provider, entry.get())
        self.settings_manager.save_settings()
        messagebox.showinfo("成功", "所有API密钥已成功保存到 app_settings.json 文件中。")

    def _set_ui_state(self, is_running):
        """Enables or disables UI elements based on whether a task is running."""
        state = "disabled" if is_running else "normal"
        self.analysis_button.configure(state=state)
        self.plot_button.configure(state=state)
        self.tab_view.configure(state=state) # Lock tabs during operation
        self.tab_view.set("① 数据挖掘" if is_running else self.tab_view.get())
        
        self.stop_button.configure(state="normal" if is_running else "disabled")
        
        if is_running:
            self.analysis_button.configure(text="挖掘中...")
        else:
            self.analysis_button.configure(text="开始挖掘")
            self.progress_bar.set(0)
            self.progress_label.configure(text="0/0")


    def _process_queue(self):
        """
        Processes messages from the background threads to update the GUI.
        This is the only safe way to interact with Tkinter widgets from other threads.
        """
        try:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                if isinstance(message, tuple) and message[0] == "progress":
                    _, current, total = message
                    progress = float(current) / float(total) if total > 0 else 0
                    self.progress_bar.set(progress)
                    self.progress_label.configure(text=f"{current}/{total}")
                elif isinstance(message, str):
                    self.log(message)
                    if any(keyword in message for keyword in ["完成", "错误", "中止", "完毕"]):
                        self._set_ui_state(is_running=False)
        except Exception as e:
            self.log(f"队列处理错误: {e}")
        finally:
            self.after(100, self._process_queue)

    # --- Thread Starters ---

    def _start_analysis_thread(self):
        """Starts the data mining process in a new thread."""
        provider = self.provider_var.get()
        model = self.model_var.get()
        api_key = self.settings_manager.get_api_key(provider)
        endpoint = API_CONFIGS.get(provider, {}).get("endpoint")
        
        input_file = self.input_entry.get()
        output_file = self.output_entry.get()
        prompt_template = self.prompt_textbox.get("0.0", "end")

        if not all([api_key, input_file, output_file, model]):
            messagebox.showerror("错误", "API密钥、模型、输入/输出文件和提示词均不能为空。请检查API设置选项卡。")
            return
        
        try:
            process_count = int(self.process_count_entry.get())
        except ValueError:
            messagebox.showerror("错误", "'处理数量' 必须是一个整数。")
            return
            
        try:
            api_client = get_api_client(provider, api_key, model, endpoint, self.queue)
        except ValueError as e:
            messagebox.showerror("API 初始化失败", str(e))
            return

        self.settings_manager.set_selected_model(provider, model)
        
        self._set_ui_state(is_running=True)
        self.log("分析任务开始...")
        thread = threading.Thread(
            target=self.data_processor.run_analysis,
            args=(api_client, input_file, output_file, process_count, prompt_template, self.resume_var.get())
        )
        thread.daemon = True
        thread.start()

    def _load_explorer_data(self):
        """Loads data for the Data Explorer tab."""
        filepath = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath: return
        
        self.explorer_entry.delete(0, "end")
        self.explorer_entry.insert(0, filepath)
        
        if self.data_explorer.load_data(filepath):
            # Update Preview
            preview_df = self.data_explorer.get_data_preview()
            self.explorer_preview_text.configure(state="normal")
            self.explorer_preview_text.delete("0.0", "end")
            self.explorer_preview_text.insert("0.0", preview_df.to_string())
            self.explorer_preview_text.configure(state="disabled")
            
            # Update Summary
            summary_text, stats_df = self.data_explorer.get_data_summary()
            self.explorer_summary_text.configure(state="normal")
            self.explorer_summary_text.delete("0.0", "end")
            self.explorer_summary_text.insert("0.0", summary_text)
            if stats_df is not None:
                self.explorer_summary_text.insert("end", stats_df.to_string())
            self.explorer_summary_text.configure(state="disabled")
            
            self.log(f"数据探索文件已加载: {os.path.basename(filepath)}")
        else:
            messagebox.showerror("错误", f"无法加载或读取文件:\n{filepath}")

    def _load_viz_data(self):
        """Loads data for the Visualization tab and updates dropdown menus."""
        filepath = self.viz_input_entry.get()
        if not filepath:
            filepath = tkinter.filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
            if not filepath: return
            self.viz_input_entry.delete(0, "end")
            self.viz_input_entry.insert(0, filepath)
        
        self.settings_manager.set("last_viz_file", filepath)

        if self.visualizer.load_data(filepath):
            column_types = self.visualizer.get_column_types()
            
            # Update menus based on data
            self.plot_option_menus["x_axis"].configure(values=column_types["categorical"] + column_types["numerical"])
            self.plot_option_menus["y_axis"].configure(values=column_types["numerical"])
            self.plot_option_menus["hue"].configure(values=column_types["categorical"])
            self.plot_option_menus["size"].configure(values=column_types["numerical"])
        else:
             messagebox.showerror("错误", f"无法为可视化加载数据:\n{filepath}")

    def _start_plot_thread(self):
        """Starts the plot generation in a new thread."""
        if self.visualizer.df is None:
            messagebox.showerror("错误", "请先加载并分析数据。")
            return
            
        plot_params = {name: var.get() for name, var in self.plot_option_vars.items()}
        plot_params["plot_type"] = self.plot_type_var.get()

        self._set_ui_state(is_running=True)
        self.log(f"正在生成图表: {plot_params['plot_type']}...")
        thread = threading.Thread(target=self.visualizer.generate_plot, args=(plot_params,))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    app = LiteratureMinerApp()
    app.mainloop()

