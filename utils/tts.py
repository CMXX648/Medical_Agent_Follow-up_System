import os
import json
import hmac
import hashlib
import base64
import time
import threading
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

"""
author: cmx x648
"""

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


class TencentTTS:
    """腾讯云实时语音合成 - 使用正确的 WebSocket 接口"""

    def __init__(self):
        self.app_id = os.getenv('TENCENT_APP_ID')
        self.secret_id = os.getenv('TENCENT_SECRET_ID')
        self.secret_key = os.getenv('TENCENT_SECRET_KEY')

        if not all([self.app_id, self.secret_id, self.secret_key]):
            raise ValueError("请设置环境变量: TENCENT_APP_ID, TENCENT_SECRET_ID, TENCENT_SECRET_KEY")

        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._done_event = threading.Event()
        self.last_error = ""
        self._ok = True

    def _build_auth(self, text: str) -> str:
        """构建 WebSocket 连接 URL（使用 stream_ws 接口）"""
        timestamp = int(time.time())
        session_id = str(uuid.uuid4()).replace('-', '')
        
        # 请求参数（按官方文档要求）
        params = {
            'Action': 'TextToStreamAudioWS',      # 接口名
            'AppId': int(self.app_id),            # 注意是 int 类型
            'SecretId': self.secret_id,
            'Timestamp': timestamp,
            'Expired': timestamp + 86400,         # 有效期24小时
            'SessionId': session_id,
            'Text': text,
            'VoiceType': 101001,                  # 音色：智瑜
            'Codec': 'pcm',                       # 音频格式
            'SampleRate': 16000,
            'Speed': 0,
            'Volume': 0,
        }
        
        # 1. 对参数按字典序排序
        sorted_params = sorted(params.items())
        
        # 2. 拼接签名原文：GET + 域名 + 路径 + ? + 参数
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_origin = f"GETtts.cloud.tencent.com/stream_ws?{param_str}"
        
        # 3. HMAC-SHA1 加密 + Base64 编码
        sign = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                sign_origin.encode('utf-8'),
                hashlib.sha1          # 官方要求 SHA1
            ).digest()
        ).decode('utf-8')
        
        # 4. 添加签名。由 urlencode 统一编码，避免重复编码或漏编码。
        params['Signature'] = sign
        
        # 5. 构建最终 URL（自动编码 Text 等参数）
        final_params = urlencode(params)
        
        return f"wss://tts.cloud.tencent.com/stream_ws?{final_params}"

    def _on_message(self, ws, message):
        """处理 WebSocket 消息"""
        if isinstance(message, bytes):
            # 二进制帧：PCM 音频数据
            if self._stream and self._stream.is_active():
                try:
                    self._stream.write(message)
                except Exception as e:
                    print(f"播放音频失败: {e}")
        else:
            # 文本帧：控制消息
            try:
                data = json.loads(message)
                code = data.get('code', -1)
                if code != 0:
                    self.last_error = data.get('message', '未知错误')
                    self._ok = False
                    print(f"\nTTS 错误: {self.last_error}")
                    self._done_event.set()
                if data.get('final') == 1:
                    self._done_event.set()
            except json.JSONDecodeError:
                pass

    def _on_error(self, ws, error):
        self.last_error = str(error)
        self._ok = False
        print(f"\nTTS WebSocket 错误: {error}")
        self._done_event.set()

    def _on_close(self, ws, close_status_code, close_msg):
        self._done_event.set()

    def _on_open(self, ws):
        pass

    def speak(self, text: str) -> bool:
        """合成并播放语音"""
        if not text or not text.strip():
            return True

        self._done_event.clear()
        self.last_error = ""
        self._ok = True

        # 打开音频流
        try:
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                output=True,
                frames_per_buffer=3200
            )
        except Exception as e:
            print(f"打开音频设备失败: {e}")
            self.last_error = str(e)
            self._ok = False
            return False

        # 连接 WebSocket
        url = self._build_auth(text)
        ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
        ws_thread.start()

        # 等待完成（超时30秒）
        self._done_event.wait(timeout=30)

        # 清理
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None

        return self._ok

    def close(self):
        """释放资源"""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
        self._pa.terminate()