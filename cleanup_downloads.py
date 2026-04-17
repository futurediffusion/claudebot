import os
import shutil
import time
from datetime import datetime, timedelta
import sys

# Añadimos el path para usar el grabador de tareas si es posible
sys.path.append(os.getcwd())
from gemini_skills.master_toolbox import TaskRecorder

def organize_downloads():
    recorder = TaskRecorder("organize_old_downloads")
    
    # 1. Ruta de descargas
    downloads_path = os.path.expanduser("~/Downloads")
    archive_name = "Archivo_Descargas_Antiguas"
    archive_path = os.path.join(downloads_path, archive_name)
    
    recorder.log_step("init", "checking_path", {"path": downloads_path})
    
    if not os.path.exists(downloads_path):
        print(f"❌ No se encontró la carpeta: {downloads_path}")
        recorder.complete("failed_path_not_found")
        return

    # 2. Calcular fecha límite (60 días atrás)
    limit_date = datetime.now() - timedelta(days=60)
    print(f"📅 Archivos anteriores al: {limit_date.strftime('%Y-%m-%d')}")
    
    # 3. Crear carpeta de archivo si no existe
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        recorder.log_step("setup", "archive_folder_created")

    # 4. Procesar archivos
    files_moved = 0
    total_size = 0
    
    recorder.log_step("processing", "scanning_files")
    
    for filename in os.listdir(downloads_path):
        file_path = os.path.join(downloads_path, filename)
        
        # Saltarse la carpeta de archivo propia y directorios (opcional)
        if filename == archive_name or os.path.isdir(file_path):
            continue
            
        # Obtener fecha de modificación
        mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mtime)
        
        if file_date < limit_date:
            try:
                # Mover archivo
                shutil.move(file_path, os.path.join(archive_path, filename))
                files_moved += 1
                total_size += os.path.getsize(os.path.join(archive_path, filename))
                print(f"📦 Movido: {filename} ({file_date.strftime('%Y-%m-%d')})")
            except Exception as e:
                print(f"⚠️ Error moviendo {filename}: {e}")

    recorder.complete(f"success_moved_{files_moved}_files")
    print(f"\n✅ ¡Limpieza completada!")
    print(f"📁 Se han movido {files_moved} archivos a la carpeta '{archive_name}'.")
    print(f"📊 Espacio organizado: {total_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    organize_downloads()
