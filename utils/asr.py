import os
import json
import hmac
import hashlib
import base64
import time
import threading
import queue
import uuid
from pathlib import Path
import pyaudio
import websocket
from urllib.parse import urlencode

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # 允许在未安装 python-dotenv 的环境中运行
    pass


def _load_local_env_file():
    env_path = Path(__file__).resolve().parents[1] / '.env'
    if not env_path.exists():
        return

    try:
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        pass


_load_local_env_file()


class TencentASR:
    """腾讯云实时语音识别"""

    # 音频参数
    CHUNK = 3200        # 每帧字节数（16kHz * 2bytes * 0.1s）
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    def __init__(self):
        self.app_id = os.getenv('TENCENT_APP_ID')
        self.secret_id = os.getenv('TENCENT_SECRET_ID')
        self.secret_key = os.getenv('TENCENT_SECRET_KEY')
        device_idx = os.getenv('TENCENT_ASR_INPUT_DEVICE_INDEX')
        self.input_device_index = int(device_idx) if device_idx and device_idx.isdigit() else None

        self.ws = None
        self.result_queue = queue.Queue()  # 存放识别结果
        self.is_speaking = False
        self.final_text = ""              # 最终识别结果
        self._stop_event = threading.Event()
        self.last_error = ""

        if not all([self.app_id, self.secret_id, self.secret_key]):
            raise ValueError("请设置环境变量: TENCENT_APP_ID, TENCENT_SECRET_ID, TENCENT_SECRET_KEY")

    # ------------------------------------------------------------------ #
    #  签名生成
    # ------------------------------------------------------------------ #
    def _build_auth(self):
        """严格按照腾讯云官方文档实现签名"""
        timestamp = int(time.time())
        
        # 1. 生成唯一的 voice_id（必填参数）
        voice_id = str(uuid.uuid4())
        
        # 2. 准备所有请求参数
        params = {
            'secretid': self.secret_id,           # 必填
            'timestamp': timestamp,               # 必填
            'expired': timestamp + 3600,          # 必填，有效期1小时
            'nonce': timestamp,                   # 必填，随机正整数
            'engine_model_type': '16k_zh',        # 必填
            'voice_id': voice_id,                 # 必填
            'voice_format': 1,                    # 可选，1=pcm
            'needvad': 1,                         # 可选，开启VAD
            'vad_silence_time': 800,              # 可选，静音断句阈值
        }
        
        # 3. 对参数按字典序排序
        sorted_items = sorted(params.items())
        
        # 4. 拼接签名原文（不包含协议 wss://）
        query_str = urlencode(sorted_items)
        sign_origin = f"asr.cloud.tencent.com/asr/v2/{self.app_id}?{query_str}"
        
        # 5. HMAC-SHA1 加密
        sign = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                sign_origin.encode('utf-8'),
                hashlib.sha1          # 注意：是 SHA1，不是 SHA256！
            ).digest()
        ).decode('utf-8')
        
        # 6. 添加签名。由 urlencode 统一编码，避免重复编码导致签名错误。
        params['signature'] = sign
        final_query_str = urlencode(params)
        url = f"wss://asr.cloud.tencent.com/asr/v2/{self.app_id}?{final_query_str}"
        
        return url

    # ------------------------------------------------------------------ #
    #  WebSocket 回调
    # ------------------------------------------------------------------ #
    def _on_message(self, ws, message):
        data = json.loads(message)
        code = data.get('code', -1)
        if code != 0:
            print(f"ASR 错误: {data.get('message')}")
            return

        result = data.get('result', {})
        text = result.get('voice_text_str', '')
        is_final = result.get('slice_type', 0) == 2  # 2 表示句子结束

        if text:
            # 实时打印（覆盖同一行）
            print(f"\r用户: {text}", end='', flush=True)

        if is_final and text:
            print()  # 换行
            self.final_text = text
            self.result_queue.put(text)  # 放入队列，主线程取用

    def _on_error(self, ws, error):
        self.last_error = str(error)
        print(f"\nASR WebSocket 错误: {error}")
        self.result_queue.put(None)

    def _on_close(self, ws, close_status_code, close_msg):
        pass

    def _on_open(self, ws):
        self.is_speaking = True

    # ------------------------------------------------------------------ #
    #  音频采集线程
    # ------------------------------------------------------------------ #
    def _record_and_send(self):
        pa = pyaudio.PyAudio()
        stream = None
        seq = 0
        try:
            stream = pa.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.CHUNK
            )
            while not self._stop_event.is_set():
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                if self.ws and self.ws.sock:
                    self.ws.send(data, websocket.ABNF.OPCODE_BINARY)
                seq += 1
        except Exception as e:
            self.last_error = f"麦克风采集失败: {e}"
            print(f"\nASR 错误: {self.last_error}")
            self.result_queue.put(None)
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            pa.terminate()
            # 发送结束帧
            if self.ws and self.ws.sock:
                self.ws.send(json.dumps({"type": "end"}))

    # ------------------------------------------------------------------ #
    #  对外接口：录一句话，返回识别文本
    # ------------------------------------------------------------------ #
    def listen(self, prompt: str = "") -> str:
        """
        开始录音，等待 VAD 检测到句子结束后返回识别文本。
        prompt: 提示用户说话的文字
        """
        if prompt:
            print(prompt, end=' ', flush=True)

        self._stop_event.clear()
        self.final_text = ""
        self.last_error = ""

        url = self._build_auth()
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        # WebSocket 在子线程跑
        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()

        # 等待连接建立
        time.sleep(0.5)

        # 音频采集在另一个子线程
        record_thread = threading.Thread(target=self._record_and_send, daemon=True)
        record_thread.start()

        # 主线程阻塞等待识别结果
        try:
            result = self.result_queue.get(timeout=30)  # 最长等30秒
        except queue.Empty:
            self.last_error = "ASR 等待超时"
            result = None

        # 停止录音
        self._stop_event.set()
        self.ws.close()

        return result or ""