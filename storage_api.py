from flask import Blueprint, jsonify, request
import gridstatus
import pandas as pd
from datetime import datetime
import logging

# --- 蓝图定义 ---
storage_api = Blueprint('storage_api', __name__)
caiso = gridstatus.CAISO()

# --- API 路由 ---

@storage_api.route('/api/storage/get_latest_storage')
def get_latest_storage():
    """
    获取当天的最新储能数据 (通常是 5 分钟间隔数据)。
    """
    try:
        logging.info("Fetching latest storage data from CAISO...")
        # 获取当天的数据
        storage_df  = caiso.get_storage(date=pd.Timestamp.now().date())
        
        if storage_df is None or storage_df.empty:
            logging.warning("No storage data available.")
            return jsonify({"error": "未找到储能数据"}), 404
        
        # 数据处理
        storage_df['Time'] = pd.to_datetime(storage_df['Time'])
        data_to_return = {
            "timestamps": storage_df['Time'].dt.strftime('%H:%M').tolist(),
            # 确保使用 'Supply' 列
            "storage_values": storage_df['Supply'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching storage data: {e}")
        return jsonify({"error": f"获取储能数据失败: {str(e)}"}), 500

@storage_api.route('/api/storage/get_history_storage')
def get_history_storage():
    """
    获取指定日期的历史储能数据。
    Query Params:
        date (str): 查询日期，格式 YYYY-MM-DD
    """
    try:
        logging.info("Fetching historical storage data from CAISO...")
        date = request.args.get('date')
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        storage_df = caiso.get_storage(date)
        
        if storage_df is None or storage_df.empty:
            logging.warning("No storage data available.")
            return jsonify({"error": "未找到历史储能数据"}), 404
            
        # 数据处理
        storage_df['Time'] = pd.to_datetime(storage_df['Time'])
        data_to_return = {
            "timestamps": storage_df['Time'].dt.strftime('%H:%M').tolist(),
            "storage_values": storage_df['Supply'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching storage data: {e}")
        return jsonify({"error": f"获取储能数据失败: {str(e)}"}), 500

# 注意：原始的 /api/storage/get_realtime_storage 路由返回的是单个瞬时值，
# 这与前端图表期望的数据系列不匹配。
# get_latest_storage 路由（获取当天数据）更适合前端使用。
# 为避免混淆，此处注释掉 get_realtime_storage。
# @storage_api.route('/api/storage/get_realtime_storage')
# def get_realtime_storage():
#     try:
#         logging.info("Fetching latest storage data from CAISO...")
#         storage_df  = caiso.get_storage(date='latest')
#         # 实时数据是一个dict结构
#         if not isinstance(storage_df, dict) or storage_df is None:
#             logging.warning("No storage data available.")
#             return jsonify({"error": "No storage data available"}), 503
        
#         dt = pd.to_datetime(storage_df['time']).strftime('%H:%M')
#         value = storage_df['supply']
#         data_to_return = {
#             "timestamps": dt,
#             "storage_values": value
#         }
#         return jsonify(data_to_return)
#     except Exception as e:
#         logging.error(f"Error fetching storage data: {e}")
#         return jsonify({"error": str(e)}), 500