import subprocess
from utility.mlogging import logger

# Constants
STATUS_NONE = -1
STATUS_STOP = 0
STATUS_RUNNING = 1

class NodeManager:
    """节点进程管理
    """
    def __init__(self, work_path: str, config_path: str):
        self.status = STATUS_STOP
        self.work_path = work_path
        self.config_path = config_path
        self.bridge_node_process = None
        self.asr_node_process = None
        self.tts_node_process = None
        self.chat_node_process = None

    def start(self):
        """启动各节点"""
        logger.info("start nodes.")
        if self.status == STATUS_RUNNING:
            logger.warn("nodes, already start.")
            return

        bridge_node_app = self.work_path + '/' + 'node_bridge.py' 
        bridge_node_config = self.config_path + '/' + 'config_bridge.json' 
        self.bridge_node_process = subprocess.Popen(['python', bridge_node_app, bridge_node_config])

        asr_node_app = self.work_path + '/' + 'node_asr.py' 
        asr_node_config = self.config_path + '/' + 'config_asr.json' 
        self.asr_node_process = subprocess.Popen(['python', asr_node_app, asr_node_config])

        chat_node_app = self.work_path + '/' + 'node_chat.py' 
        chat_node_config = self.config_path + '/' + 'config_chat.json' 
        self.chat_node_process = subprocess.Popen(['python', chat_node_app, chat_node_config])

        tts_node_app = self.work_path + '/' + 'node_tts.py' 
        tts_node_config = self.config_path + '/' + 'config_tts.json' 
        self.tts_node_process = subprocess.Popen(['python', tts_node_app, tts_node_config])

        self.status = STATUS_RUNNING

    def stop(self):
        """关闭各节点"""
        logger.info("close nodes.")
        if self.status == STATUS_STOP:
            logger.warn("nodes, already stop.")
            return

        self.bridge_node_process.terminate()
        self.bridge_node_process.wait()

        self.asr_node_process.terminate()
        self.asr_node_process.wait()

        self.chat_node_process.terminate()
        self.chat_node_process.wait()

        self.tts_node_process.terminate()
        self.tts_node_process.wait()

        self.status = STATUS_STOP

    def restart(self):
        """重启各节点"""
        logger.info("restart nodes.")
        if self.status == STATUS_RUNNING:
            self.stop()
        self.start() 