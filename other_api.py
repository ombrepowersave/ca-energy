from flask import Blueprint, jsonify, request
import gridstatus
import pandas as pd
from datetime import datetime
import logging

# --- 蓝图定义 ---
# 注意：此蓝图 'other_api' 未在 app.py 中注册
# 如果需要使用此 API，请在 app.py 中添加：
# from other_api import other_api
# app.register_blueprint(other_api)
other_api = Blueprint('other_api', __name__)
caiso = gridstatus.CAISO()

# --- API 路由 ---

@other_api.route('/api/other/get_curtailment')
def get_curtailment():
    """
    获取指定日期的削峰（Curtailment）数据。
    Query Params:
        date (str): 查询日期，格式 YYYY-MM-DD
    """
    try:
        logging.info("Fetching curtailment data from CAISO...")
        date = request.args.get('date')
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
            
        curtailment_df = caiso.get_curtailment(date)
        
        if curtailment_df is None or curtailment_df.empty:
            logging.warning("No curtailment data available.")
            return jsonify({"error": "未找到削峰数据"}), 404
            
        # 数据处理
        curtailment_df['Time'] = pd.to_datetime(curtailment_df['Time'])
        data_to_return = {
            "timestamps": curtailment_df['Time'].dt.strftime('%H:%M').tolist(),
            # 确保使用 'Curtailment' 列
            "curtailment_values": curtailment_df['Curtailment'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching curtailment data: {e}")
        return jsonify({"error": f"获取削峰数据失败: {str(e)}"}), 500