# coding=utf-8
## coding=utf-8
# node_chat.py

import sys
import json
from time import sleep
from collections import deque

import torch
from transformers import pipeline
import websocket

# 1. 日志系统初始化
from utility import mlogging
mlogging.logger_config('chat', mlogging.INFO, False)
from utility.mlogging import logger

from mq_base_node import MqBaseNode, mq_close

# =================================
# Optional: Separate chat wrappers
# =================================
class OpenAIChat:
    """Mock example to preserve interface from original code."""
    def __init__(self, config):
        self.config = config
        # In reality, you'd call openai API here with self.config["model"], etc.
    def get_response_stream(self, text):
        # Example generator
        yield {"seq": 1, "text": f"[OpenAIChat Stream] {text}"}
    def get_response(self, text):
        return {"seq": 1, "text": f"[OpenAIChat Non-Stream] {text}"}
    def decode_chunk(self, chunk):
        return chunk

class HuggingFaceChat:
    """Local Hugging Face wrapper."""
    def __init__(self, config):
        device = 0 if torch.cuda.is_available() else -1
        self.text_pipeline = pipeline("text-generation", 
                                      model=config.get("model", "gpt2"), 
                                      device=device)
        self.sentiment_pipeline = pipeline("sentiment-analysis", device=device)
    def get_response_stream(self, text):
        # If you have a streaming approach, you'd chunk the outputs.
        # For demo, just yield one chunk.
        result = self.text_pipeline(text, max_length=50, truncation=True)[0]['generated_text']
        yield {"seq": 1, "text": result}
    def get_response(self, text):
        result = self.text_pipeline(text, max_length=50, truncation=True)[0]['generated_text']
        return {"seq": 1, "text": result}
    def decode_chunk(self, chunk):
        return chunk
    def analyze_sentiment(self, text):
        sentiment = self.sentiment_pipeline(text)[0]['label']  # 'POSITIVE'/'NEGATIVE'/'NEUTRAL' (as 'NEUTRAL' sometimes becomes 'POSITIVE' or 'NEGATIVE')
        return sentiment

class DeepSeekChat:
    """DeepSeek local model wrapper."""
    def __init__(self, config):
        device = 0 if torch.cuda.is_available() else -1
        self.text_pipeline = pipeline("text-generation", 
                                      model=config.get("model", "./models/phi-2"),
                                      device=device)
        self.sentiment_pipeline = pipeline("sentiment-analysis", device=device)
    def get_response_stream(self, text):
        result = self.text_pipeline(text, max_length=50, truncation=True)[0]['generated_text']
        yield {"seq": 1, "text": result}
    def get_response(self, text):
        result = self.text_pipeline(text, max_length=50, truncation=True)[0]['generated_text']
        return {"seq": 1, "text": result}
    def decode_chunk(self, chunk):
        return chunk
    def analyze_sentiment(self, text):
        sentiment = self.sentiment_pipeline(text)[0]['label']
        return sentiment

# =================================
# The ChatNode
# =================================
class ChatNode(MqBaseNode):
    def __init__(self, config: dict):
        super().__init__(config['rabbitmq'])
        self.chat_config = config['chat']

        # Max queue length
        self.que_max_len = 5000
        self.set_que_max_len(self.que_max_len)

        # Chat session trackers
        self.chat_id = 0
        self.cancel_chat_id = -1
        self.node_exit = False

        # Decide which chat implementation to load
        service = self.chat_config.get("service", "openai").lower()
        if service == "huggingface":
            logger.info("👉 Using HuggingFaceChat for local inference.")
            self.chat_impl = HuggingFaceChat(self.chat_config.get("huggingface", {}))
        elif service == "":
            logger.info("👉 Using PHI-2 for local inference.")
            self.chat_impl = DeepSeekChat(self.chat_config.get("deepseek", {}))
        else:
            logger.info("👉 Using OpenAIChat (original).")
            self.chat_impl = OpenAIChat(self.chat_config.get("openai", {}))

        # Optionally set up a separate pipeline or rely on self.chat_impl's sentiment method
        self.enable_eye_animations = self.chat_config.get("enable_eyes", False)
        self.esp32_ws_url = self.chat_config.get("esp32_ws_url", "ws://<ESP32-IP>:<PORT>")

    @mq_close
    def close(self):
        self.node_exit = True
        logger.info("🔴 Chat node shutting down...")

    def create_answer_msg(self, msg: dict, chat_id: int):
        return {
            'node': "chat",
            'topic': "chat/answer",
            'type': "json",
            'data': {
                'chat_id': chat_id,
                'seq': msg['seq'],
                'text': msg['text'],
            }
        }

    def handle_mq_msg(self, msg: dict, stream=True):
        """
        We keep the original logic:
         - check for cancel
         - handle asr/response
         - optionally do streaming
        """
        topic = msg.get('topic', '')
        if topic == 'request/cancel':
            self.cancel_chat_id = msg['data']['chat_id']
            logger.info(f'Received cancel signal. Current chat_id={self.chat_id}, cancel_chat_id={self.cancel_chat_id}')
        elif topic == 'asr/response':
            text = msg['data']['text']
            self.chat_id = msg['data']['chat_id']
            logger.info(f'🎤 User: {text}')

            # Check if canceled
            if self.chat_id <= self.cancel_chat_id:
                logger.info(f'⚠️ Chat {self.chat_id} canceled (<= {self.cancel_chat_id}). Skipping.')
                return

            if stream:
                # Streamed approach
                response_stream = self.chat_impl.get_response_stream(text)
                for chunk in response_stream:
                    answer_msg = self.chat_impl.decode_chunk(chunk)  # from original code
                    if answer_msg is not None:
                        logger.info(f"🤖 AI (stream seq={answer_msg['seq']}): {answer_msg['text']}")
                        self.auto_send(self.create_answer_msg(answer_msg, self.chat_id))
                        # optional sentiment per chunk
                        if self.enable_eye_animations:
                            sentiment = self.chat_impl.analyze_sentiment(answer_msg['text'])
                            self.send_emotion_to_eyes(sentiment)
            else:
                # Non-streamed approach
                answer_msg = self.chat_impl.get_response(text)
                logger.info(f"🤖 AI: {answer_msg['text']}")
                self.auto_send(self.create_answer_msg(answer_msg, self.chat_id))

                # Eye animations
                if self.enable_eye_animations:
                    sentiment = self.chat_impl.analyze_sentiment(answer_msg['text'])
                    self.send_emotion_to_eyes(sentiment)

    def send_emotion_to_eyes(self, sentiment):
        """Sends an emotion-based eye animation command to ESP32 via WebSocket."""
        emotion = self.map_emotion_to_eyes(sentiment)
        logger.info(f"👀 Sending emotion to ESP32: {emotion}")

        try:
            ws = websocket.WebSocket()
            ws.connect(self.esp32_ws_url)
            ws.send(json.dumps({"emotion": emotion}))
            ws.close()
        except Exception as e:
            logger.error(f"❌ ERROR sending eye animation: {e}")

    @staticmethod
    def map_emotion_to_eyes(sentiment_label):
        emotion_map = {
            "POSITIVE": "HAPPY",
            "NEGATIVE": "SAD",
            "NEUTRAL": "NEUTRAL"
        }
        # If the pipeline sometimes returns something like "LABEL_1", you might need a small fix here.
        # For now, assume it returns "POSITIVE", "NEGATIVE", or "NEUTRAL".
        return emotion_map.get(sentiment_label.upper(), "NEUTRAL")

    def launch(self):
        self.transport_start()
        while not self.node_exit:
            # read from MQ
            mq_msg = self.auto_read()
            if mq_msg:
                # Original code used 'stream=True' by default
                self.handle_mq_msg(mq_msg, stream=True)
            sleep(0.001)


def main(config: dict):
    chat_node = ChatNode(config)
    chat_node.launch()


if __name__ == '__main__':
    logger.info('🚀 Chat node starting...')
    if len(sys.argv) < 2:
        logger.error('❌ ERROR: Usage: python node_chat.py <config_file>')
        sys.exit(1)
    config_file = sys.argv[1]
    logger.info(f'📄 Loading config: {config_file}')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info(config)
            main(config)
    except Exception as e:
        logger.error(f'❌ ERROR loading config: {e}')
        sys.exit(1)
