# coding=utf-8
# 在线TTS节点
import sys
import base64
import json
from time import sleep
#1.日志系统初始化,配置log等级
from utility import mlogging
mlogging.logger_config('tts', mlogging.INFO, False)

from transformers import pipeline
from mq_base_node import MqBaseNode, mq_close
import websocket
# from utility.keyboard import KBHit
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts")

from mq_base_node import MqBaseNode, mq_close
from tts.volc_tts import VolcTTS
from tts.xfai_tts import XFaiTTS
# Load sentiment model
sentiment_analyzer = pipeline("sentiment-analysis")

class TTSNode(MqBaseNode):
    """tts节点
    """
    def __init__(self, config: dict):
        """初始化
        Args:
            config  app参数配置信息
        """
        # rabbitmq初始化
        super().__init__(config['rabbitmq']) 
        # rabbitmq接收缓冲队列最大长度
        self.set_que_max_len(5000)

        self.tts_config = config['tts']
        self.audio_format = self.tts_config['common']['audio']['codec']
        self.audio_samplerate = self.tts_config['common']['audio']['samplerate']
        self.audio_channels = self.tts_config['common']['audio']['channels']

        # 键盘控制
        # self.keyboard = KBHit()
        self.node_exit = False

        # tts实例
        self.tts = None
        service = self.tts_config['service']
        if service == 'volc':
            self.tts = VolcTTS(config=self.tts_config)
        elif service == 'xfai':
            self.tts = XFaiTTS(config=self.tts_config)
        else:
            logger.error('invalid tts service: {}'.format(service))

        # 单次TTS请求文本长度限制为 1024 字节(不要超出服务商API要求的限制)
        self._tts_text_bytes_max = 1024

        # 音频数据缓冲区大小(固定,需要和硬件API匹配)
        self._audio_frame_length = 512
        self._audio_frame_buff = b''

        # 聊天语句缓冲
        self.chat_answers = ''
        # 前n句直接合成，不等待
        self.direct_n = self.tts_config['common']['direct_n']

        # 本轮聊天ID
        self.chat_id = 0
        # 已取消的聊天ID
        self.cancel_chat_id = -1

    @mq_close
    def close(self):
        """关闭节点
        """
        self.tts.close()
        self.node_exit = True
        logger.info('app exit')

    def create_response_msg(self, chat_id: int, chat_end: int, seg_end: int, text=None, audio=None):
        """创建响应消息
        Args:
            chat_id: 本轮聊天ID
            chat_end: 1 or 0, 响应完全结束
            seg_end: 1 or 0, 一段结束
            text:  本次合成的文本(一次请求的完整文本，并未对应语音片段)
            audio: 合成的音频数据 
        Note:
            确保整体数据包长度不超过硬件设定值,默认(2048)
        """
        data_obj = {
            'node': self.node_name,
            'topic': "chat/response",
            'type': "json",
            'data':{
                'chat_id': chat_id,  
                'chat_end': chat_end,  
                'seg_end': seg_end,  
            }    
        }
        if text is not None:
            ## TODO: 未防止包大小超出最大值,需要控制text文本长度,需要改为分句发送
            # data_obj['data']['text'] = text
            data_obj['data']['text'] = ' '
        if audio is not None:
            # 对音频数据进行base64编码
            audiob64 = base64.b64encode(audio).decode()
            # print(audiob64)
            data_obj['data']['audio'] = {
                "samplerate": self.audio_samplerate,
                "bits": 16, 
                "channels": self.audio_channels, 
                "format": self.audio_format,
                "buff": audiob64
            }
        return data_obj


    def create_voice_type_msg(self, voice_type: dict):
        """创建voice_type消息
        Args:
            voice_type 数据 
        """
        data_obj = {
            "node": "tts",  
            "topic": "tts/voice_type",
            "type": "json",
            "data": voice_type
        }
        return data_obj


    def send_voice_types(self):
        """读取并发送所有音色消息
        """
        types = self.tts_config['volc']['voice_types']
        for _ in range(3):  # 确保消息收到 
            sleep(0.1)
            for type in types: 
                msg = self.create_voice_type_msg(type)
                # print(msg)
                self.auto_send(msg)
                sleep(0.005)
        logger.info('pub all voice type info.')

    def voice_types_test(self, voice_type_index: int):
        """音色播放测试
        """
        types = self.tts_config['volc']['voice_types']
        print(types)
        if voice_type_index < 0:
            for type in types: 
                self.execute(type['example_text'], type['id'])
        else:
            type = types[voice_type_index]
            self.execute(type['example_text'], type['id'])


    def _process_audio_frame(self, audio: bytes, flush=False):
        """处理音频数据
        1. 数据帧处理,限制帧长
        Args:
            audio:  音频数据 
            flush:  是否清空缓冲区剩余数据
        Returns:
            frames: 音频数据帧列表，含n帧数据
        """
        frames = []
        self._audio_frame_buff += audio

        # 每次循环处理一帧长度的音频数据
        while len(self._audio_frame_buff) >= self._audio_frame_length:
            # 从音频缓冲区中取出一帧长度的数据
            frame = self._audio_frame_buff[:self._audio_frame_length]
            frames.append(frame)  # 将取出的帧数据加入帧列表
            self._audio_frame_buff = self._audio_frame_buff[self._audio_frame_length:]  # 更新音频缓冲区

        if flush and len(self._audio_frame_buff) > 0:
            # 如果开启了 flush
            # padding = bytes([0] * (self._audio_frame_length - len(self._audio_frame_buff)))
            frame = self._audio_frame_buff 
            frames.append(frame)
            self._audio_frame_buff = b''  # 清空音频缓冲区

        return frames


    def _clear_audio_frame(self):
        """清空音频缓冲区
        """
        self._audio_frame_buff = b''


    def send_response_msg(self, msg: str):
        """处理和发送TTS响应结果
        Args:
            msg          待发送的消息
        """
        ## 如果聊天已经取消,则不发送该消息
        if self.chat_id <= self.cancel_chat_id:
            logger.info('this chat already cancel, no send reponse msg, chat_id: {}, cancel chat_id: {}'.format(self.chat_id, self.cancel_chat_id))
            return
        self.auto_send(msg)


    def handle_tts_result(self, text: str, end_sentence):
        """循环处理TTS响应结果
           TODO: 增加超时退出
        Args:
            text: 合成的文本
            end_sentence: 是否为尾句
        Returns:
            True 合成成功  False合成失败(不重试) 
        """
        finished = False
        while not finished:
            sleep(0.01)  # 等待n ms
            logger.debug('handle tts result loop.')
            res = self.tts.get_result()
            if res is None:
                continue

            if 'status' not in res:
                logger.warning('tts response invaild.')
                self.tts.connect_close()
                self._clear_audio_frame()
                return False

            # print(2,res)
            if res['status'] == 'DISCONNECT':
                self._clear_audio_frame()
                # 进行自动重连
                self.tts.auto_connect()
                timeout = 10000
                sleep_time = 0.01
                sleep_count = 0
                while True:
                    sleep(sleep_time)
                    sleep_count += 1
                    res = self.tts.get_result()
                    if res is None:
                        continue
                    if res['status'] == "CONNECTED":
                        logger.info('auto reconnect success.')
                        break
                    if sleep_time*sleep_count > timeout:
                        logger.error('ws auto reconnect fail, timeout.')
                        return False

            if res['status'] != 'REQ_OK':
                logger.info('status is not req_ok, is: {}'.format(res['status']))
                continue

            ret = res['result']
            logger.info("synthesis bytes: {}".format(ret['seq_size']))

            ## 获取音频帧
            frames = []
            if ret['status'] == 0:
                logger.info("synthesis start...")
                continue
                # frames = self._process_audio_frame(ret['data'])
            elif ret['status'] == 1:  # 合成中间段 
                frames = self._process_audio_frame(ret['data'])

            elif ret['status'] == 2:   # 合成结束
                frames = self._process_audio_frame(ret['data'], flush=True)
                finished = True

            elif ret['status'] == -1:  # 合成失败
                logger.warning("synthesis fail, clear frame buff.")
                self._clear_audio_frame()
                return False
            logger.info('get audio frames: {}'.format(len(frames)))

            # 发生数据帧时间间隔(ms)  
            send_dt = 0.005
            ## 正常结束   
            if finished: 
                ## 循环发送数据帧
                for frame in frames[0:-1]:
                    msg = self.create_response_msg(self.chat_id, chat_end=0, seg_end = 0, text=text, audio=frame)
                    self.send_response_msg(msg)
                    sleep(send_dt)
                ## 发送尾帧
                msg = None
                if end_sentence:  ## 本次聊天结束
                    msg = self.create_response_msg(self.chat_id, chat_end=1, seg_end = 1, text=text, audio=frames[-1])
                    # self.tts.connect_close() ## 暂时不关闭,有问题
                else:  ## 本段结束
                    msg = self.create_response_msg(self.chat_id, chat_end=0, seg_end = 1, text=text, audio=frames[-1])
                # 发送帧消息
                self.send_response_msg(msg)
                return True
            else:
                ## 循环发送数据帧
                for frame in frames:
                    msg = self.create_response_msg(self.chat_id, chat_end=0, seg_end = 0, text=text, audio=frame)
                    self.send_response_msg(msg)
                    sleep(send_dt)


    def execute(self, text: str, voice_type=None, operation_type = None, end_sentence = False):
        """执行TTS,并发布结果
        Args:
            text:  要合成的文本
            voice_type:  要选择的音色
            operation_type   'query' or 'submit' 单次返回或者流式返回 
            end_sentence: 是否为尾句
        """
        ## 处理空文本转为合法提交,提交合成
        logger.info('start synthesis: {}'.format(text))
        if text == '' or text == ' ':
            logger.info('empty str, return')
            return
        # 设置音色        
        if voice_type is not None:
            self.tts.set_voice_type(voice_type)
        # 设置返回方式       
        if operation_type is not None:
            self.tts.set_operation_type(operation_type)

        # 提交合成
        self.tts.execute(text)

        # 等待并处理合成结果(阻塞)
        logger.info('synthesis execute, start handing')
        ret = self.handle_tts_result(text, end_sentence)
        if ret == False:  ## 合成失败,放弃这次合成操作
            logger.warning('synthesis fail.')
        logger.info('synthesis end.')


    def handle_mq_msg(self, msg: dict):
        """Handles Text-to-Speech (TTS) and Eye Animations.

        Args:
            msg: Received message from RabbitMQ.
        """
        logger.debug("Received MQ message, topic: {}".format(msg['topic']))

        ## Handle Chat Cancel Request
        if msg['topic'] == 'request/cancel':
            self.cancel_chat_id = msg['data']['chat_id']
            logger.info(f'Received cancel signal, chat_id: {self.chat_id}, cancel_chat_id: {self.cancel_chat_id}')
            return

        ## Direct TTS Request (Bypassing Chatbot)
        elif msg['topic'] == 'request/tts':
            self.execute(msg['data']['text'], msg['data'].get('voice_type'))
            return

        ## Process Chatbot Response for TTS & Eye Animation
        elif msg['topic'] == 'chat/answer':
            answer = msg['data']
            answer_text = answer['text']
            self.chat_id = answer['chat_id']

            logger.info(f'Processing TTS for chat_id: {self.chat_id}')

            ## If chat was canceled before processing, ignore
            if self.chat_id <= self.cancel_chat_id:
                logger.info(f'This chat was canceled, skipping TTS, chat_id: {self.chat_id}, cancel_chat_id: {self.cancel_chat_id}')
                self.chat_answers = ''
                return

            # 🔥 New Feature: Analyze Sentiment for Eye Animations
            sentiment = sentiment_analyzer(answer_text)[0]['label']
            send_emotion_to_eyes(sentiment)

            ## Handle TTS Processing
            if answer['seq'] >= 0:
                # Process direct responses (first `direct_n` messages)
                if answer['seq'] < self.direct_n:
                    self.execute(text=answer_text)
                else:
                    # Merge messages to reduce TTS requests
                    text_bytes_size = len(self.chat_answers.encode('utf-8')) + len(answer_text.encode('utf-8'))
                    logger.info(f'TTS text buffer size: {text_bytes_size}')
                    
                    if text_bytes_size > self._tts_text_bytes_max:
                        self.execute(text=self.chat_answers)
                        self.chat_answers = ''
                    
                    self.chat_answers += answer_text

            else:  # **End of Conversation**
                self.chat_answers += answer_text

                if not self.chat_answers:
                    msg = self.create_response_msg(self.chat_id, chat_end=1, seg_end=1)
                    self.auto_send(msg)
                else:
                    self.execute(text=self.chat_answers, end_sentence=True)

                self.chat_answers = ''


    @staticmethod
    def send_emotion_to_eyes(sentiment):
        """Send emotion-based eye animation to ESP32-S3."""
        emotion = TTSNode.map_emotion_to_eyes(sentiment)
        try:
            ws = websocket.WebSocket()
            ws.connect("ws://<ESP32-IP>:<PORT>")  # Replace with your ESP32’s IP and port
            # Send as JSON for consistency with other nodes:
            ws.send(json.dumps({"emotion": emotion}))
            ws.close()
        except Exception as e:
            logger.error("Failed to send emotion to ESP32: {}".format(e))

    @staticmethod
    def map_emotion_to_eyes(sentiment):
        """Map sentiment to ESP32 eye animations."""
        if sentiment == "POSITIVE":
            return "HAPPY"
        elif sentiment == "NEGATIVE":
            return "SAD"
        else:
            return "NEUTRAL"
        
    def launch(self):
        """TTS主任务
        """
        ## 启动rabbbitmq传输子线程
        self.transport_start()

        ## 启动tts
        self.tts.launch()

        ## 默认设置为流式响应
        self.tts.set_operation_type(operation_type='submit')
        # self.execute('这是一段话，用于语音合成测试,1+1=2, 3+3=6', operation_type='submit')

        ## 广播音频类型数据
        self.send_voice_types()

        ## 音色合成语音测试
        # self.voice_types_test(-1)

        while not self.node_exit:
            logger.debug('tts main loop.')
            # await asyncio.sleep(0.01)
            sleep(0.01)
            # self.keyboard_control()
            ## 获取接收队列数据
            mq_msg = self.auto_read()
            if mq_msg is not None:
                self.handle_mq_msg(mq_msg)


    def test(self):
        self.tts.execute(' 这是一段话，用于语音合成测试.')
        ## 等待查询合成结果
        while True:
            sleep(0.1)
            ret = self.tts.get_result()
            if ret is not None:
                print(ret['status'])


def main(config: dict):
    """入口函数
    """
    tts_node = TTSNode(config)
    # tts_node.test()
    tts_node.launch()


if __name__=='__main__':
    """APP入口
    """
    logger.info('tts node start...')

    #读取配置文件
    if len(sys.argv) < 2:
        logger.error('useage: config_file')
        exit(0)

    config_file = sys.argv[1]
    logger.info('config: %s', config_file)

    with open(config_file, 'r', encoding='utf-8') as load_f:
        config = json.load(load_f)
        logger.info(config)
        # asyncio.run(main(config))
        main(config)
