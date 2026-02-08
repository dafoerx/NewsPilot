# src/workflows/run_daily_report.py
"""
生成每日报表 (Daily Report Task)
职责：
1. 计算正确的统计时间窗口 (昨天 8:00 BM - 今天 8:00 AM)
2. 调用 Analyzer 生成全量报表
该脚本通常由系统定时任务 (Cron/Task Scheduler) 调用，也可手动运行。
"""
import asyncio
import os
import sys
from datetime import datetime, time, timedelta

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from src.intelligence.new_analyzer import NewsAnalyzer

# Config

async def main(save_dir: str, model_name: str = "gemini", report_time: time = time(8, 0)):
    """
    运行日报生成任务
    :param save_dir: 报告保存目录
    :param model_name: 使用的模型名称 (gemini, deepseek, etc.)
    :param report_time: 结算时间点 (默认 08:00)
    """
    print(f"\n🚀 Starting Daily Report Task [Model: {model_name}]")
    
    analyzer = NewsAnalyzer(model_name=model_name)
    
    # Calculate Time Window (Yesterday 8:00 AM -> Today 8:00 AM)
    now = datetime.now()
    today_cutoff = datetime.combine(now.date(), report_time)
    
    # Check if run before the cutoff time
    if now.time() < report_time:
        print(f"⚠️  Early Run: Current time {now.strftime('%H:%M')} < {report_time}. Generating PREVIEW.")
    
    yesterday_cutoff = today_cutoff - timedelta(days=1)
    
    print(f"📅 Time Window: {yesterday_cutoff} -> {today_cutoff}")
    print(f"📂 Output Dir: {save_dir}\n")

    try:
        await analyzer.generate_all_daily_reports(
            target_date=now.date(),
            save_path=save_dir,
            time_range=(yesterday_cutoff, today_cutoff)
        )
        print("\n✅ Report Generation Completed.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    if sys.platform.startswith('win'):
        # 解决 Windows 上 EventLoop 关闭时的 RuntimeError
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        # Default Configuration: Output to project_root/data/reports/...
        DEFAULT_SAVE_DIR = os.path.join(project_root, "data", 'daily_reports')
        
        asyncio.run(main(
            save_dir=DEFAULT_SAVE_DIR,
            model_name="gemini",
            report_time=time(8, 0)
        ))
    except KeyboardInterrupt:
        print("\n👋 Task Cancelled.")
