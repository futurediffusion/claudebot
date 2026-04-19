import subprocess
import json
import sys
import os

class MediaSurgical:
    def __init__(self):
        self.ffmpeg = "ffmpeg"

    def execute_command(self, cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return {"status": "success", "output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": e.stderr}

    def extract_audio(self, input_file, output_format="mp3"):
        output_file = f"{os.path.splitext(input_file)[0]}.{output_format}"
        cmd = [self.ffmpeg, "-i", input_file, "-vn", "-acodec", "libmp3lame", "-y", output_file]
        return self.execute_command(cmd)

    def trim_media(self, input_file, start_time, duration):
        output_file = f"trimmed_{os.path.basename(input_file)}"
        cmd = [self.ffmpeg, "-ss", str(start_time), "-i", input_file, "-t", str(duration), "-c", "copy", "-y", output_file]
        return self.execute_command(cmd)

    def gpu_upscale(self, input_file):
        """Mejora de imagen usando el motor de GPU NVIDIA (si esta disponible)"""
        output_file = f"upscaled_{os.path.basename(input_file)}"
        # Usamos scale_npp para escalado por hardware NVIDIA
        cmd = [
            self.ffmpeg, "-i", input_file, 
            "-vf", "scale=iw*2:ih*2", # Escalado 2x (simple por ahora)
            "-c:v", "h264_nvenc", # Forzamos el uso de la GPU para el encoding
            "-y", output_file
        ]
        return self.execute_command(cmd)

def run_mcp_loop():
    cirujano = MediaSurgical()
    print("--- MEDIA SURGICAL MCP SERVER ONLINE ---")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            
            input_file = params.get("input")
            
            if method == "extract_audio":
                result = cirujano.extract_audio(input_file)
            elif method == "trim":
                result = cirujano.trim_media(input_file, params.get("start"), params.get("duration"))
            elif method == "gpu_upscale":
                result = cirujano.gpu_upscale(input_file)
            else:
                result = {"error": "Metodo no soportado"}
            
            print(json.dumps({"result": result}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    run_mcp_loop()
