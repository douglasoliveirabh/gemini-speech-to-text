#!/usr/bin/env python3
import os
import glob
import subprocess
from pathlib import Path

def is_media_file(filename):
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv']
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg']
    all_extensions = video_extensions + audio_extensions
    return any(filename.lower().endswith(ext) for ext in all_extensions)

def is_video_file(filename):
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ogv']
    return any(filename.lower().endswith(ext) for ext in video_extensions)

def convert_to_mp3(video_file, output_file):
    cmd = [
        'ffmpeg', '-i', video_file, 
        '-vn', '-acodec', 'mp3', '-ab', '128k', 
        '-ar', '44100', '-y', output_file
    ]
    subprocess.run(cmd, check=True)

def get_audio_duration(audio_file):
    cmd = [
        'ffprobe', '-v', 'quiet', '-show_entries', 
        'format=duration', '-of', 'csv=p=0', audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def split_audio(audio_file, output_dir):
    duration = get_audio_duration(audio_file)
    segment_duration = 30 * 60  # 30 minutos em segundos
    
    base_name = Path(audio_file).stem
    segments = []
    
    start_time = 0
    segment_num = 1
    
    while start_time < duration:
        remaining_time = duration - start_time
        current_segment_duration = min(segment_duration, remaining_time)
        
        output_file = os.path.join(output_dir, f"{base_name}-{segment_num:02d}.mp3")
        
        cmd = [
            'ffmpeg', '-i', audio_file, 
            '-ss', str(start_time), 
            '-t', str(current_segment_duration),
            '-acodec', 'copy', '-y', output_file
        ]
        
        subprocess.run(cmd, check=True)
        segments.append(output_file)
        
        start_time += segment_duration
        segment_num += 1
    
    return segments

def process_videos():
    arquivo_dir = "arquivo"
    mp3_dir = "mp3"
    
    if not os.path.exists(arquivo_dir):
        print(f"Diretório {arquivo_dir} não encontrado!")
        return
    
    os.makedirs(mp3_dir, exist_ok=True)
    
    media_files = []
    for file_path in glob.glob(os.path.join(arquivo_dir, "*")):
        if os.path.isfile(file_path) and is_media_file(file_path):
            media_files.append(file_path)
    
    if not media_files:
        print("Nenhum arquivo de mídia encontrado no diretório arquivo/")
        return
    
    for media_file in media_files:
        print(f"Processando: {os.path.basename(media_file)}")
        
        base_name = Path(media_file).stem
        
        try:
            if is_video_file(media_file):
                print("  Convertendo vídeo para MP3...")
                temp_mp3 = os.path.join(mp3_dir, f"{base_name}_temp.mp3")
                convert_to_mp3(media_file, temp_mp3)
                audio_to_split = temp_mp3
            else:
                print("  Arquivo já é áudio, pulando conversão...")
                audio_to_split = media_file
            
            print("  Dividindo em segmentos de 30 minutos...")
            segments = split_audio(audio_to_split, mp3_dir)
            
            if is_video_file(media_file):
                os.remove(temp_mp3)
            
            print(f"  Criados {len(segments)} segmentos:")
            for segment in segments:
                print(f"    {os.path.basename(segment)}")
                
        except subprocess.CalledProcessError as e:
            print(f"  Erro ao processar {media_file}: {e}")
        except Exception as e:
            print(f"  Erro inesperado ao processar {media_file}: {e}")

if __name__ == "__main__":
    process_videos()