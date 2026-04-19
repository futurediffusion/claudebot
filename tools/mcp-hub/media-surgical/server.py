import subprocess
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("media-surgical")

_FFMPEG = "ffmpeg"


def _run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr}


@mcp.tool()
def extract_audio(input_file: str, output_format: str = "mp3") -> dict:
    """Extrae la pista de audio de un video y la guarda como mp3 (u otro formato)."""
    output_file = f"{os.path.splitext(input_file)[0]}.{output_format}"
    cmd = [_FFMPEG, "-i", input_file, "-vn", "-acodec", "libmp3lame", "-y", output_file]
    return _run_cmd(cmd)


@mcp.tool()
def trim_media(input_file: str, start_time: str, duration: str) -> dict:
    """Recorta un video/audio desde start_time durante duration segundos."""
    output_file = f"trimmed_{os.path.basename(input_file)}"
    cmd = [_FFMPEG, "-ss", start_time, "-i", input_file, "-t", duration, "-c", "copy", "-y", output_file]
    return _run_cmd(cmd)


@mcp.tool()
def gpu_upscale(input_file: str) -> dict:
    """Escala un video x2 usando h264_nvenc (GPU NVIDIA). Salida: upscaled_<nombre>."""
    output_file = f"upscaled_{os.path.basename(input_file)}"
    cmd = [_FFMPEG, "-i", input_file, "-vf", "scale=iw*2:ih*2", "-c:v", "h264_nvenc", "-y", output_file]
    return _run_cmd(cmd)


if __name__ == "__main__":
    mcp.run()
