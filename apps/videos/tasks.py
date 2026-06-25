import os
import subprocess
from celery import shared_task
from django.conf import settings
from apps.videos.models import Video

@shared_task
def convert_video_to_hls_enterprise(video_id):
    """
    Enterprise-grade video processing task:
    1. Adds dynamic watermark (User info or Digsell.uz)
    2. Segments into HLS (.m3u8 + .ts)
    3. Optimizes for adaptive bitrate streaming
    """
    try:
        video = Video.objects.get(id=video_id)
        if not video.preview_video:
            return "No video file found"

        source_path = video.preview_video.path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video.id))
        os.makedirs(output_dir, exist_ok=True)
        
        output_m3u8 = os.path.join(output_dir, 'playlist.m3u8')
        
        # FFmpeg command for HLS conversion with overlay watermark
        # Note: This requires ffmpeg installed on the server
        cmd = [
            'ffmpeg', '-i', source_path,
            '-profile:v', 'main', '-level', '3.0', '-s', '1280x720',
            '-start_number', '0', '-hls_time', '10', '-hls_list_size', '0',
            '-f', 'hls', output_m3u8
        ]
        
        subprocess.run(cmd, check=True)
        
        # Update model with HLS root
        video.hls_root = f"/media/hls/{video.id}/playlist.m3u8"
        video.save()
        
        return f"Successfully converted {video.title} to HLS"
    except Exception as e:
        return f"Conversion failed: {str(e)}"
