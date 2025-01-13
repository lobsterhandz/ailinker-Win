from flask import Flask, render_template, jsonify
import os
from utility.mlogging import logger
from node_manager import NodeManager  # Import the NodeManager class

# Constants
STATUS_NONE = -1
STATUS_STOP = 0
STATUS_RUNNING = 1

# Get work and config paths
WORK_PATH = os.environ.get("AILINKER_WORK_PATH", None)
if WORK_PATH is None:
    logger.error("get work path fail, please execute: source env_setup.bash")
    exit(1)
CONFIG_PATH = WORK_PATH + "/configs/config"

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')

manager = NodeManager(work_path=WORK_PATH, config_path=CONFIG_PATH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/device/info')
def get_device_info():
    device_info = {
        'name': 'AI-VOICE-Z01',
        'status': False
    }
    return jsonify(device_info)

@app.route('/nodes_start', methods=['GET'])
def start_node():
    manager.start()
    return jsonify({'status': STATUS_RUNNING}), 200

@app.route('/nodes_stop', methods=['GET'])
def stop_node():
    manager.stop()
    return jsonify({'status': STATUS_STOP}), 200

@app.route('/nodes_restart', methods=['GET'])
def restart_node():
    manager.restart()
    return jsonify({'status': STATUS_RUNNING}), 200

def close_nodes():
    """关闭各nodes"""
    manager.stop()

if __name__ == '__main__':
    logger.info("main app start...")
    app.run(debug=True, host='0.0.0.0', port=8090)
    close_nodes()
