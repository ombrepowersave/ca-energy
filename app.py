from flask import Flask, render_template
import logging

# 导入各个功能的蓝图（Blueprints）
from lmp_api import lmp_api
from load_api import load_api
from storage_api import storage_api
# from other_api import other_api # 注意：other_api.py 存在，但未在此处注册，如需使用请取消注释

# --- 应用初始化 ---

# 初始化 Flask 应用
app = Flask(__name__)

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# --- 蓝图注册 ---
# 将各个 API 模块注册到主应用中
app.register_blueprint(lmp_api)
app.register_blueprint(load_api)
app.register_blueprint(storage_api)
# app.register_blueprint(other_api) # 如需使用 other_api，请取消此行注释

# --- 页面路由 (View Routes) ---

@app.route('/')
def index():
    """
    渲染项目首页。
    """
    return render_template('index.html')

@app.route('/lmp')
def lmp_page():
    """
    渲染 LMP (节点边际电价) 详情页面。
    """
    return render_template('lmp.html')

@app.route('/load')
def load_page():
    """
    渲染电网负荷详情页面。
    """
    return render_template('load.html')

@app.route('/storage')
def storage_page():
    """
    渲染储能详情页面。
    """
    return render_template('storage.html')

# --- 启动入口 ---

if __name__ == '__main__':
    # 以调试模式运行应用
    # debug=True 会在代码变更后自动重启服务
    # 在生产环境中应将其设置为 False
    app.run(debug=True, port=5000)