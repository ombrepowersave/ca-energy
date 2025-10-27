from flask import Blueprint, jsonify, request
import gridstatus
import pandas as pd
from datetime import datetime
import logging

# --- 蓝图定义 ---
# 创建一个名为 'lmp_api' 的蓝图
lmp_api = Blueprint('lmp_api', __name__)
# 初始化 CAISO 客户端
caiso = gridstatus.CAISO()

# --- API 路由 ---

@lmp_api.route('/api/locations')
def get_lmp_locations():
    """
    获取所有可用的 LMP 交易中心位置。
    这些位置用于历史LMP查询。
    """
    try:
        locations = caiso.trading_hub_locations
        return jsonify({"locations": locations})
    except Exception as e:
        logging.error(f"Error fetching LMP locations: {e}")
        return jsonify({"error": f"获取位置失败: {str(e)}"}), 500

@lmp_api.route('/api/get_history_lmp')
def get_history_lmp():
    """
    获取指定日期和地点的历史 LMP 数据。
    Query Params:
        date (str): 查询日期，格式 YYYY-MM-DD
        location (str): 查询的地点名称 (从 /api/locations 获取)
    """
    try:
        logging.info("Fetching historical LMP data from CAISO...")
        date = request.args.get('date')
        location = request.args.get('location')

        # 参数校验
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        if not location:
            return jsonify({"error": "必须提供 location (地区) 参数"}), 400

        # 获取数据 (日度、小时级市场)
        lmp_df = caiso.get_lmp(date, market=gridstatus.Markets.DAY_AHEAD_HOURLY)
        
        if lmp_df is None or lmp_df.empty:
            logging.warning("No LMP data available.")
            return jsonify({"error": "未找到LMP数据"}), 404

        # 数据处理
        # 注意：原始代码获取了所有地点的LMP，但没有按请求的 'location' 过滤
        # 这里我们加入过滤步骤
        lmp_df_filtered = lmp_df[lmp_df['Location'] == location]
        
        if lmp_df_filtered.empty:
            logging.warning(f"No LMP data for location {location}.")
            return jsonify({"error": f"未找到地区 {location} 的LMP数据"}), 404

        lmp_df_filtered['Time'] = pd.to_datetime(lmp_df_filtered['Time'])
        
        # 格式化返回数据
        data_to_return = {
            "timestamps": lmp_df_filtered['Time'].dt.strftime('%H:%M').tolist(),
            "lmp_values": lmp_df_filtered['LMP'].tolist()
        }
        return jsonify(data_to_return)
        
    except Exception as e:
        logging.error(f"Error fetching LMP data: {e}")
        return jsonify({"error": f"获取LMP数据失败: {str(e)}"}), 500

# 注意：原始的 /api/lmp 路由获取的是 'TH_NP15_GEN-APND' 的 'latest' 数据
# 这在 lmp.html 页面中并未使用。
# 如果需要，可以保留或移除。为保持完整性，暂时保留并添加注释。
@lmp_api.route('/api/lmp')
def get_lmp_data():
    """
    获取最新的 (latest) LMP 数据，固定地点 'TH_NP15_GEN-APND'。
    (注意: 此接口未在 lmp.html 中使用)
    """
    try:
        logging.info("Fetching latest LMP data from CAISO...")
        lmp_df = caiso.get_lmp(date='latest', market=gridstatus.Markets.DAY_AHEAD_HOURLY, locations=['TH_NP15_GEN-APND'])
        
        if lmp_df is None or lmp_df.empty:
            logging.warning("No LMP data available.")
            return jsonify({"error": "未找到LMP数据"}), 404
            
        lmp_df['Time'] = pd.to_datetime(lmp_df['Time'])
        data_to_return = {
            "timestamps": lmp_df['Time'].dt.strftime('%H:%M').tolist(),
            "lmp_values": lmp_df['LMP'].tolist()
        }
        return jsonify(data_to_return)
    except Exception as e:
        logging.error(f"Error fetching LMP data: {e}")
        return jsonify({"error": f"获取LMP数据失败: {str(e)}"}), 500