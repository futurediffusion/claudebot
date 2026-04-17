import os
import shutil
import sys

# Añadimos el path para usar el grabador de tareas
sys.path.append(os.getcwd())
from gemini_skills.master_toolbox import TaskRecorder

def classify_by_extension():
    recorder = TaskRecorder("classify_old_downloads")
    
    archive_path = os.path.expanduser("~/Downloads/Archivo_Descargas_Antiguas")
    
    if not os.path.exists(archive_path):
        print(f"❌ No se encontró la carpeta: {archive_path}")
        return

    recorder.log_step("init", "scanning_extensions")
    
    files_processed = 0
    folders_created = set()

    for filename in os.listdir(archive_path):
        file_path = os.path.join(archive_path, filename)
        
        # Ignorar directorios (solo queremos clasificar archivos sueltos)
        if os.path.isdir(file_path):
            continue
            
        # Obtener extensión
        name, ext = os.path.splitext(filename)
        ext = ext.lower().replace(".", "")
        
        if not ext:
            ext = "Sin_Extension"
            
        # Carpeta de destino (ej: JPG_Files)
        target_folder_name = f"{ext.upper()}_Archivos"
        target_folder_path = os.path.join(archive_path, target_folder_name)
        
        # Crear carpeta si no existe
        if not os.path.exists(target_folder_path):
            os.makedirs(target_folder_path)
            folders_created.add(target_folder_name)
            
        # Mover archivo
        try:
            shutil.move(file_path, os.path.join(target_folder_path, filename))
            files_processed += 1
        except Exception as e:
            print(f"⚠️ Error moviendo {filename}: {e}")

    recorder.complete(f"success_processed_{files_processed}_files")
    print(f"\n✅ ¡Clasificación completada!")
    print(f"📁 Se han creado {len(folders_created)} tipos de carpetas.")
    print(f"📦 {files_processed} archivos organizados por tipo.")
    if folders_created:
        print(f"Tipos detectados: {', '.join(list(folders_created)[:10])}...")

if __name__ == "__main__":
    classify_by_extension()
