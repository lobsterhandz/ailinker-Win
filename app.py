from flask import Flask, render_template, jsonify, request
import os
import subprocess
import threading
import sys
import json
from flask_socketio import SocketIO
from dotenv import load_dotenv
from utility.mlogging import logger
import logging
# Additional imports for AI pipelines and GPU detection
import torch
from transformers import pipeline

# =============================================================================
# Load Environment Variables
# =============================================================================
load_dotenv()

# Detect GPU availability
device = 0 if torch.cuda.is_available() else "cpu"

# =============================================================================
# Constants & Paths
# =============================================================================
STATUS_NONE = -1
STATUS_STOP = 0
STATUS_RUNNING = 1
PORT = 8090  # Keep original AiLinker port for compatibility

WORK_PATH = os.getenv("AILINKER_WORK_PATH")
if WORK_PATH is None:
    logger.error("❌ ERROR: Work path missing. Please check your .env file.")
    exit(1)

CONFIG_PATH = os.path.join(WORK_PATH, "configs/config")
# Configure Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s]: %(message)s")

# =============================================================================
# Initialize Flask App & SocketIO
# =============================================================================
app = Flask(__name__,
            template_folder='web/templates',
            static_folder='web/static')

socketio = SocketIO(app, cors_allowed_origins="*")

# =============================================================================
# Node Manager (Original AiLinker Functionality)
# =============================================================================
class NodeManager:
    """Manages AI Nodes (ASR, Chat, TTS)"""
    def __init__(self, work_path: str, config_path: str):
        self.status = STATUS_STOP
        self.work_path = work_path
        self.config_path = config_path
        self.processes = {}

    def start(self):
        """Start AI Nodes"""
        logger.info("🟢 Starting Nodes...")
        if self.status == STATUS_RUNNING:
            logger.warning("⚠️ Nodes are already running.")
            return

        try:
            node_scripts = {
                "bridge": "node_bridge.py",
                "asr": "node_asr.py",
                "chat": "node_chat.py",
                "tts": "node_tts.py"
            }
            for key, script in node_scripts.items():
                process = subprocess.Popen(
                    [sys.executable, f"{self.work_path}/{script}", f"{self.config_path}/config_{key}.json"]
                )
                self.processes[key] = process

            self.status = STATUS_RUNNING
            logger.info("✅ Nodes started successfully.")
        except Exception as e:
            logger.error(f"❌ ERROR Starting Nodes: {e}")

    def stop(self):
        """Stop AI Nodes"""
        logger.info("🛑 Stopping Nodes...")
        if self.status == STATUS_STOP:
            logger.warning("⚠️ Nodes are already stopped.")
            return

        for key, process in self.processes.items():
            if process:
                process.terminate()
                process.wait()

        self.processes.clear()
        self.status = STATUS_STOP

    def restart(self):
        """Restart AI Nodes"""
        logger.info("🔄 Restarting Nodes...")
        self.stop()
        self.start()

# Initialize Node Manager
try:
    manager = NodeManager(work_path=WORK_PATH, config_path=CONFIG_PATH)
    logger.info("✅ Node Manager Initialized Successfully")
except Exception as e:
    logger.error(f"❌ ERROR Initializing Node Manager: {e}")
    exit(1)

# =============================================================================
# Load AI Models for Chat & Sentiment Analysis
# =============================================================================
try:
    chatbot = pipeline("text-generation", 
                   model="./models/phi-2", 
                   device=device,
                   torch_dtype=torch.float16)  # Use float16 for speed

    # Load Sentiment Analyzer (DistilBERT)
    sentiment_analyzer = pipeline("sentiment-analysis",
                                  model="distilbert-base-uncased-finetuned-sst-2-english",
                                  device=0 if torch.cuda.is_available() else -1)  # Ensure correct device

    logger.info("✅ AI Models Loaded Successfully")
except Exception as e:
    logger.error(f"❌ ERROR Loading AI Models: {e}")
    chatbot, sentiment_analyzer = None, None

# =============================================================================
# WebSocket Handlers for ESP32 (Eye Animation)
# =============================================================================
@socketio.on('connect', namespace='/ws/eyes')
def ws_connect():
    logger.info("🟢 ESP32 Connected to WebSocket.")

@socketio.on('disconnect', namespace='/ws/eyes')
def ws_disconnect():
    logger.warning("🔴 ESP32 Disconnected from WebSocket.")

@socketio.on("eye_animation", namespace='/ws/eyes')
def handle_eye_animation(data):
    """Handle incoming eye animation events from ESP32 or clients."""
    logger.info(f"👀 Eye Animation Received: {data}")

def send_eye_command(emotion):
    """Send emotion command to ESP32 via WebSocket."""
    try:
        socketio.emit('eye_animation', {'emotion': emotion}, namespace='/ws/eyes')
        logger.info(f"👀 Sent Eye Animation: {emotion}")
    except Exception as e:
        logger.error(f"❌ ERROR Sending Eye Animation: {e}")

def map_emotion_to_eyes(sentiment):
    """Map sentiment to ESP32 eye animations."""
    emotion_map = {
        "POSITIVE": "HAPPY",
        "NEGATIVE": "SAD",
        "NEUTRAL": "NEUTRAL"
    }
    return emotion_map.get(sentiment.upper(), "NEUTRAL")

# =============================================================================
# API Routes
# =============================================================================


@app.before_request
def log_request():
    """Logs all incoming HTTP requests for debugging"""
    logging.info(f"🔹 Request: {request.method} {request.url}")
    logging.info(f"🔹 Headers: {request.headers}")

@app.after_request
def log_response(response):
    """Logs all responses sent to ESP32"""
    logging.info(f"🔸 Response: {response.status}")
    return response

@app.route('/favicon.ico')
def favicon():
    """Prevent 415 errors from missing favicon requests"""
    return '', 204

@app.route('/api/device/info', methods=['GET'])
def get_device_info():
    """Returns device information"""
    device_info = {
        'name': 'AI-VOICE-Z01',
        'status': True  
    }
    return jsonify(device_info)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nodes_start', methods=['GET'])
def start_node():
    """Starts AiLinker nodes"""
    try:
        manager.start()
        return jsonify({'status': STATUS_RUNNING}), 200
    except Exception as e:
        logger.error(f"❌ ERROR Starting Nodes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/nodes_stop', methods=['GET'])
def stop_node():
    """Stops AiLinker nodes"""
    try:
        manager.stop()
        return jsonify({'status': STATUS_STOP}), 200
    except Exception as e:
        logger.error(f"❌ ERROR Stopping Nodes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/nodes_restart', methods=['GET'])
def restart_node():
    """Restarts AiLinker nodes"""
    try:
        manager.restart()
        return jsonify({'status': STATUS_RUNNING}), 200
    except Exception as e:
        logger.error(f"❌ ERROR Restarting Nodes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ws_test', methods=['POST'])
def ws_test():
    """Manually send a test WebSocket message to ESP32."""
    try:
        message = request.json.get("message", "TEST")
        socketio.emit('eye_animation', {"message": message}, namespace='/ws/eyes')
        return jsonify({"status": "✅ Message Sent", "message": message})
    except Exception as e:
        logger.error(f"❌ ERROR Sending WebSocket Test Message: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Additional Eye/Chat Routes
# ---------------------------
@app.route('/api/chat', methods=['POST'])
def chat():
    """Chatbot API to handle user messages and trigger eye animations."""
    if chatbot is None:
        return jsonify({"error": "❌ AI Model Not Loaded"}), 500

    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "❌ Empty Message Sent"}), 400

        # Generate AI Response
        response_data = chatbot(user_input, max_length=50, truncation=True)
        response_text = response_data[0]['generated_text']

        # Analyze Sentiment
        sentiment_data = sentiment_analyzer(response_text)
        sentiment_label = sentiment_data[0]['label']
        emotion = map_emotion_to_eyes(sentiment_label)

        # Send Emotion Command to ESP32
        send_eye_command(emotion)

        return jsonify({
            "response": response_text,
            "sentiment": sentiment_label,
            "eye_animation": emotion
        })
    except Exception as e:
        logger.error(f"❌ ERROR in Chatbot Processing: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/emotion', methods=['POST'])
def send_emotion():
    """API to manually trigger ESP32 eye animations."""
    try:
        emotion = request.json.get("emotion", "").strip()
        if not emotion:
            return jsonify({"error": "❌ Invalid Emotion"}), 400

        send_eye_command(emotion)
        return jsonify({"status": "✅ Emotion Sent", "emotion": emotion})
    except Exception as e:
        logger.error(f"❌ ERROR Sending Emotion: {e}")
        return jsonify({"error": str(e)}), 500

# =============================================================================
# Graceful Shutdown
# =============================================================================
def close_nodes():
    """Shutdown all nodes safely."""
    try:
        manager.stop()
        logger.info("🛑 Nodes Stopped Successfully")
    except Exception as e:
        logger.error(f"❌ ERROR Stopping Nodes: {e}")

# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == '__main__':
    try:
        logger.info("🚀 Main app starting...")
        # Use Flask-SocketIO to run both HTTP and WebSockets on the same process
        socketio.run(app, debug=True, host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"❌ Critical Failure: {e}")
    finally:
        close_nodes()
