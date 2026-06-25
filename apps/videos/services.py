import os
import hmac
import hashlib
from django.conf import settings
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from django.utils import timezone
from subprocess import CalledProcessError, run


def make_video_token(user_id, video_id, expires_seconds: int = 3600) -> str:
    s = URLSafeTimedSerializer(settings.SECRET_KEY, salt='video-access')
    return s.dumps({'user_id': user_id, 'video_id': video_id})


def verify_video_token(token: str, max_age: int = 3600):
    s = URLSafeTimedSerializer(settings.SECRET_KEY, salt='video-access')
    try:
        data = s.loads(token, max_age=max_age)
        return data
    except SignatureExpired:
        return None
    except BadSignature:
        return None


def convert_to_hls(source_path: str, dest_dir: str, watermark_text: str = "Digsell.uz"):
    """
    Convert given video file to HLS with a watermark using ffmpeg.
    """
    os.makedirs(dest_dir, exist_ok=True)
    master = os.path.join(dest_dir, 'master.m3u8')
    
    # FFMPEG filter for watermark
    # drawtext filter: fontfile should be provided or use default. 
    # For Windows, we might need to specify a path like C\\:/Windows/Fonts/arial.ttf
    # We will use a simple drawtext that works on most systems if possible.
    filter_complex = f"drawtext=text='{watermark_text}':x=10:y=10:fontsize=24:fontcolor=white@0.5:box=1:boxcolor=black@0.2"
    
    cmd = [
        'ffmpeg', '-y', '-i', source_path,
        '-vf', filter_complex,
        '-preset', 'veryfast', '-g', '48', '-sc_threshold', '0',
        '-c:v', 'libx264', '-b:v', '1500k', '-c:a', 'aac',
        '-f', 'hls', '-hls_time', '6', '-hls_playlist_type', 'vod',
        '-hls_segment_filename', os.path.join(dest_dir, 'segment_%03d.ts'),
        master
    ]
    try:
        run(cmd, check=True)
    except CalledProcessError:
        raise
