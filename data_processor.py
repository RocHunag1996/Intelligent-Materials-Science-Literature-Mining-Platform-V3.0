# 4_data_processor.py
"""
This module contains the core logic for the literature analysis process.
It handles reading data, managing the thread pool for concurrent API calls,
processing results, and saving the output. It's designed to run in a separate
thread to keep the GUI responsive.
"""
import pandas as pd
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from typing import Dict, Any

# Import from other project modules
from config import MAX_WORKERS, REQUEST_SUBMISSION_DELAY, SAVE_INTERVAL, REQUIRED_INPUT_COLUMNS
from utils import read_csv_robustly, flatten_json_result
from api_clients import BaseAPIClient

class DataProcessor:
    """
    Handles the entire data processing pipeline in a non-blocking way.
    """
    def __init__(self, queue: Queue):
        """
        Initializes the DataProcessor.

        Args:
            queue (Queue): The queue for communicating with the main GUI thread.
        """
        self.queue = queue
        self._stop_event = False

    def stop(self):
        """Signals the processing thread to stop."""
        self.queue.put("任务中止信号已发送...")
        self._stop_event = True

    def run_analysis(self, api_client: BaseAPIClient, input_file: str, output_file: str, 
                     process_count: int, prompt_template: str, resume_mode: bool):
        """
        The main method for running the analysis. This should be the target of a thread.
        """
        self._stop_event = False
        try:
            self._execute_analysis(api_client, input_file, output_file, process_count, prompt_template, resume_mode)
        except Exception as e:
            self.queue.put(f"严重错误: 分析过程中出现意外错误: {e}")
        finally:
            if self._stop_event:
                self.queue.put("分析任务已中止。")
            else:
                self.queue.put("分析流程执行完毕。")


    def _execute_analysis(self, api_client: BaseAPIClient, input_file: str, output_file: str, 
                          process_count: int, prompt_template: str, resume_mode: bool):
        """
        The core logic for the literature analysis pipeline.
        """
        df = read_csv_robustly(input_file, self.queue)
        if df is None:
            return

        self.queue.put(f"成功读取文件: {os.path.basename(input_file)}, 找到 {len(df)} 篇文章。")

        # Validate required columns
        if not all(col in df.columns for col in REQUIRED_INPUT_COLUMNS):
            self.queue.put(f"错误: CSV 文件必须包含以下列: {', '.join(REQUIRED_INPUT_COLUMNS)}")
            return

        # Handle resume mode
        processed_uids = set()
        if resume_mode and os.path.exists(output_file):
            try:
                df_out = read_csv_robustly(output_file, self.queue)
                if df_out is not None and 'UID' in df_out.columns:
                    processed_uids = set(df_out['UID'].dropna())
                    self.queue.put(f"续跑模式: 在输出文件中找到 {len(processed_uids)} 条已处理的记录。")
            except Exception as e:
                 self.queue.put(f"警告: 无法读取输出文件以进行续跑检查: {e}")
        
        if 'UID' not in df.columns:
            self.queue.put("警告: 输入文件中缺少 'UID' 列。将使用索引作为唯一标识符，续跑模式可能不准确。")
            df['UID'] = df.index
            
        df_to_process = df[~df['UID'].isin(processed_uids)]

        # Apply process count limit
        if process_count > 0:
            df_to_process = df_to_process.head(process_count)
        
        total_to_process = len(df_to_process)
        if total_to_process == 0:
            self.queue.put("所有文章均已处理，无需操作。")
            return
            
        self.queue.put(f"将要处理 {total_to_process} 篇新文章。")

        batch_results = []
        # Check if output file exists and has content to decide on writing header
        header_written = os.path.exists(output_file) and os.path.getsize(output_file) > 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            self.queue.put(f"启动 {MAX_WORKERS} 个工作线程进行并行分析...")
            future_to_uid = {}
            for index, row in df_to_process.iterrows():
                if self._stop_event: break
                
                title = row[REQUIRED_INPUT_COLUMNS[0]]
                abstract = row.get(REQUIRED_INPUT_COLUMNS[1], '')
                uid = row['UID']

                future = executor.submit(self._analyze_single_document, api_client, title, abstract, prompt_template, uid)
                future_to_uid[future] = (uid, index)
                time.sleep(REQUEST_SUBMISSION_DELAY)

            processed_count = 0
            for future in as_completed(future_to_uid):
                if self._stop_event:
                    # Cancel remaining futures
                    for f in future_to_uid:
                        f.cancel()
                    break

                uid, index = future_to_uid[future]
                try:
                    result_json = future.result()
                    
                    if result_json:
                        flat_result = flatten_json_result(result_json)
                        original_data = df.loc[index].to_dict()
                        combined_row = {**original_data, **flat_result}
                        batch_results.append(combined_row)
                    else:
                         # Handle API failure after retries
                        original_data = df.loc[index].to_dict()
                        error_row = {**original_data, "error": "API Failure after retries"}
                        batch_results.append(error_row)

                except Exception as exc:
                    self.queue.put(f"错误: 处理 UID {uid} 时出现异常: {exc}")
                    original_data = df.loc[index].to_dict()
                    error_row = {**original_data, "error": str(exc)}
                    batch_results.append(error_row)
                
                processed_count += 1
                self.queue.put(("progress", processed_count, total_to_process))

                if len(batch_results) >= SAVE_INTERVAL:
                    self._save_batch_results(batch_results, output_file, not header_written)
                    header_written = True  # Header is now written
                    batch_results.clear()
        
        # Save any remaining results in the last batch
        if batch_results:
            self._save_batch_results(batch_results, output_file, not header_written)
        
        self.queue.put(f"\n分析完成！所有结果已追加至: {output_file}")


    def _analyze_single_document(self, api_client: BaseAPIClient, title: str, abstract: str, prompt_template: str, uid: Any) -> Dict[str, Any]:
        """
        Analyzes a single literature document.
        """
        if pd.isna(title) or not title.strip():
            self.queue.put(f"跳过 UID {uid}: 标题缺失。")
            return {"error": "Missing Title"}
            
        content_to_analyze = f"Title: {title}\n\nAbstract: {abstract or ''}"
        
        try:
            prompt = prompt_template.format(content_to_analyze=content_to_analyze)
        except KeyError:
            self.queue.put("错误: 提示词模板缺少必需的 {content_to_analyze} 占位符。")
            return {"error": "Invalid Prompt Template"}
        
        self.queue.put(f"正在分析 UID {uid}: {title[:60]}...")
        return api_client.analyze_text(prompt)

    def _save_batch_results(self, batch_results, output_file, write_header):
        """
        Saves a batch of results to the output CSV file.
        """
        if not batch_results: return

        self.queue.put(f"正在保存 {len(batch_results)} 条中间结果...")
        try:
            df_batch = pd.DataFrame(batch_results)
            df_batch.to_csv(output_file, mode='a', header=write_header, index=False, encoding='utf-8-sig')
            self.queue.put("保存成功。")
        except Exception as e:
            self.queue.put(f"错误: 保存中间结果时失败: {e}")
