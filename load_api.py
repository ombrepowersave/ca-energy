from flask import Blueprint, jsonify, request
import gridstatus
import pandas as pd
from datetime import datetime
import logging

# --- 蓝图定义 ---
load_api = Blueprint('load_api', __name__)
caiso = gridstatus.CAISO()

# --- 辅助函数 ---

def _process_forecast_dataframe(df):
    """
    处理从 gridstatus 获取的负荷预测 DataFrame 的通用逻辑。
    - 确保时间列存在
    - 转换时间格式
    """
    if 'Time' not in df.columns:
        if 'Interval Start' in df.columns:
            df['Time'] = df['Interval Start']
        else:
            logging.warning("No 'Time' or 'Interval Start' column in forecast data.")
            raise ValueError("No valid time column in forecast data")
    
    df['Time'] = pd.to_datetime(df['Time'])
    return df

def _fetch_forecast_data(date, option):
    """
    根据选项获取不同类型的负荷预测数据。
    """
    if option == 'hourly':
        return caiso.get_load_forecast_day_ahead(date)
    elif option == '5min':
        return caiso.get_load_forecast_5_min(date)
    elif option == '15min':
        return caiso.get_load_forecast_15_min(date)
    else:
        # 默认返回 'hourly'
        return caiso.get_load_forecast_day_ahead(date)

# --- API 路由 ---

@load_api.route('/api/load/get_latest_date')
def get_latest_load():
    """
    获取最新的实时电网负荷数据。
    """
    try:
        logging.info("Fetching latest load data from CAISO...")
        load_df = caiso.get_load(date='latest')
        
        if load_df is None or load_df.empty:
            logging.warning("No load data available.")
            return jsonify({"error": "未找到实时负荷数据"}), 404
            
        load_df['Time'] = pd.to_datetime(load_df['Time'])
        data_to_return = {
            "timestamps": load_df['Time'].dt.strftime('%H:%M').tolist(),
            "load_values": load_df['Load'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching load data: {e}")
        return jsonify({"error": f"获取负荷数据失败: {str(e)}"}), 500

@load_api.route('/api/load/get_history_date')
def get_history_load():
    """
    获取指定日期的历史电网负荷数据。
    Query Params:
        date (str): 查询日期，格式 YYYY-MM-DD
    """
    try:
        logging.info("Fetching historical load data from CAISO...")
        date = request.args.get('date')
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        load_df = caiso.get_load(date)
        
        if load_df is None or load_df.empty:
            logging.warning("No load data available.")
            return jsonify({"error": "未找到历史负荷数据"}), 404
            
        load_df['Time'] = pd.to_datetime(load_df['Time'])
        data_to_return = {
            "timestamps": load_df['Time'].dt.strftime('%H:%M').tolist(),
            "load_values": load_df['Load'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching load data: {e}")
        return jsonify({"error": f"获取负荷数据失败: {str(e)}"}), 500
    
@load_api.route('/api/load/get_load_forecast')
def get_load_forecast():
    """
    获取指定日期的负荷预测数据 (仅限 CA ISO-TAC 区域)。
    Query Params:
        date (str): 查询日期，格式 YYYY-MM-DD
        option (str): 预测类型 ('hourly', '5min', '15min')
    """
    try:
        logging.info("Fetching load forecast data from CAISO...")
        date = request.args.get('date')
        option = request.args.get('option')
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        load_forecast_df = _fetch_forecast_data(date, option)
          
        if load_forecast_df is None or load_forecast_df.empty:
            logging.warning("No load forecast data available.")
            return jsonify({"error": "未找到负荷预测数据"}), 404
        
        # 过滤 CA ISO-TAC 区域
        load_forecast_df = load_forecast_df[load_forecast_df["TAC Area Name"] == "CA ISO-TAC"]
        if load_forecast_df.empty:
            logging.warning("No load forecast data for 'CA ISO-TAC'.")
            return jsonify({"error": "未找到 'CA ISO-TAC' 区域的预测数据"}), 404

        load_forecast_df = load_forecast_df.drop(columns=["TAC Area Name"])
        
        # 处理时间列
        load_forecast_df = _process_forecast_dataframe(load_forecast_df)

        data_to_return = {
            "timestamps": load_forecast_df['Time'].dt.strftime('%H:%M').tolist(),
            "load_forecast_values": load_forecast_df['Load Forecast'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching load forecast data: {e}")
        return jsonify({"error": f"获取负荷预测数据失败: {str(e)}"}), 500


@load_api.route('/api/load/get_all_load_forecast')
def get_all_load_forecast():
    """
    获取指定日期的所有区域负荷预测数据。
    Query Params:
        date (str): 查询日期，格式 YYYY-MM-DD
        option (str): 预测类型 ('hourly', '5min', '15min')
    """
    try:
        logging.info("Fetching all regions load forecast data from CAISO...")
        date = request.args.get('date')
        option = request.args.get('option')
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        load_forecast_df = _fetch_forecast_data(date, option)
          
        if load_forecast_df is None or load_forecast_df.empty:
            logging.warning("No load forecast data available.")
            return jsonify({"error": "未找到负荷预测数据"}), 404
        
        # 检查所需列
        if "TAC Area Name" not in load_forecast_df.columns:
            logging.warning("No 'TAC Area Name' column in forecast data.")
            return jsonify({"error": "预测数据中缺少 'TAC Area Name' 列"}), 500

        # 处理时间列
        load_forecast_df = _process_forecast_dataframe(load_forecast_df)

        # 按区域分组
        result = {}
        for area_name, group in load_forecast_df.groupby("TAC Area Name"):
            group = group.copy()
            result[area_name] = {
                "timestamps": group['Time'].dt.strftime('%H:%M').tolist(),
                "load_forecast_values": group['Load Forecast'].tolist()
            }
            
        if not result:
            return jsonify({"error": "分组后无有效数据"}), 500
            
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching load forecast data: {e}")
        return jsonify({"error": f"获取负荷预测数据失败: {str(e)}"}), 500