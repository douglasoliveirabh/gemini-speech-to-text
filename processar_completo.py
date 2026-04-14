#!/usr/bin/env python3
import os
import json
import time
import subprocess
import glob
import google.genai as genai
from pathlib import Path
from docx import Document
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar a API do Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODELS = os.getenv('GEMINI_MODELS', 'gemini-2.5-pro,gemini-2.0-flash,gemini-1.5-pro,gemini-1.5-flash').split(',')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '10'))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))
SEGMENT_DURATION_MINUTES = int(os.getenv('SEGMENT_DURATION_MINUTES', '15'))

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env")
client = genai.Client(api_key=GEMINI_API_KEY)

# Estatísticas dos modelos
model_stats = {model: {'failures': 0, 'last_503': 0} for model in GEMINI_MODELS}

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
        '-vn',  # Sem vídeo
        '-c:a', 'libmp3lame',  # Codec específico
        '-b:a', '128k',  # Bitrate
        '-ar', '44100',  # Sample rate
        '-f', 'mp3',  # Forçar formato
        '-avoid_negative_ts', 'make_zero',  # Lidar com timestamps
        '-y', output_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    # Verificar se o arquivo foi criado corretamente
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        raise Exception(f"Conversão falhou: arquivo não criado ou vazio")
    
    return result

def get_audio_duration(audio_file):
    cmd = [
        'ffprobe', '-v', 'quiet', '-show_entries', 
        'format=duration', '-of', 'csv=p=0', audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def split_audio(audio_file, output_dir):
    duration = get_audio_duration(audio_file)
    segment_duration = SEGMENT_DURATION_MINUTES * 60  # Configurável via .env
    
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

def process_media_files():
    """Processa arquivos de vídeo/áudio e divide em segmentos"""
    print("🎬 ETAPA 1: Processando arquivos de mídia...")
    
    arquivo_dir = "arquivo"
    mp3_dir = "mp3"
    
    if not os.path.exists(arquivo_dir):
        print(f"❌ Diretório {arquivo_dir} não encontrado!")
        return False
    
    os.makedirs(mp3_dir, exist_ok=True)
    
    media_files = []
    for file_path in glob.glob(os.path.join(arquivo_dir, "*")):
        if os.path.isfile(file_path) and is_media_file(file_path):
            media_files.append(file_path)
    
    if not media_files:
        print("❌ Nenhum arquivo de mídia encontrado no diretório arquivo/")
        return False
    
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
            
            print(f"  Dividindo em segmentos de {SEGMENT_DURATION_MINUTES} minutos...")
            segments = split_audio(audio_to_split, mp3_dir)
            
            if is_video_file(media_file):
                os.remove(temp_mp3)
            
            print(f"  ✅ Criados {len(segments)} segmentos")
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erro ao processar {media_file}: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Erro inesperado ao processar {media_file}: {e}")
            return False
    
    return True

def is_retryable_error(error):
    """Verifica se o erro é recuperável"""
    error_str = str(error).lower()
    if '503' in error_str or 'unavailable' in error_str or 'high demand' in error_str:
        return True, 503
    elif '429' in error_str or 'quota' in error_str or 'rate limit' in error_str:
        return True, 429
    return False, 0

def get_best_model():
    """Retorna o melhor modelo disponível"""
    now = time.time()
    
    # Filtrar modelos que não tiveram 503 nos últimos 10 minutos
    available_models = []
    for model in GEMINI_MODELS:
        last_503 = model_stats[model]['last_503']
        if now - last_503 > 600:  # 10 minutos
            available_models.append(model)
    
    if not available_models:
        # Se todos estão indisponíveis, usar o menos problemático
        available_models = [min(GEMINI_MODELS, key=lambda m: model_stats[m]['failures'])]
    
    return available_models[0]

def upload_audio_file(file_path):
    """Upload do arquivo de áudio para o Gemini com retry"""
    print(f"    Fazendo upload de {os.path.basename(file_path)}...")
    
    for attempt in range(MAX_RETRIES):
        try:
            upload_response = client.files.upload(
                path=file_path,
                config={'display_name': os.path.basename(file_path)}
            )
            
            file_uri = upload_response.uri
            time.sleep(5)  # Pequena pausa para garantir processamento
            return file_uri
            
        except Exception as e:
            is_retryable, error_code = is_retryable_error(e)
            print(f"    ⚠️ Upload tentativa {attempt + 1} falhou: {e}")
            
            if not is_retryable or attempt == MAX_RETRIES - 1:
                raise e
            
            wait_time = RETRY_DELAY * (2 ** attempt)  # Backoff exponencial
            print(f"    ⏳ Aguardando {wait_time}s...")
            time.sleep(wait_time)

def identify_personas(first_audio_file):
    """Identifica as personas no primeiro arquivo de áudio"""
    print("  🎭 Identificando personas no primeiro arquivo...")
    
    file_uri = upload_audio_file(first_audio_file)
    
    prompt = """
Analise este áudio e identifique todas as pessoas que falam durante a conversa.

Para cada pessoa, forneça:
1. Um nome/identificador simples (ex: Pessoa 1, Pessoa 2, ou se mencionado o nome real)
2. Características distintivas da voz (tom, velocidade, etc.)
3. Contexto/papel na conversa (se aparente)

Responda APENAS em formato JSON válido:
{
  "personas": [
    {
      "id": "Pessoa1",
      "nome": "Nome ou identificador",
      "caracteristicas": "Descrição da voz e características",
      "papel": "Papel na conversa se identificável"
    }
  ]
}

Seja preciso e objetivo. Não adicione texto explicativo fora do JSON.
"""
    
    # Tentar com múltiplos modelos
    for model in GEMINI_MODELS:
        for attempt in range(3):  # 3 tentativas por modelo
            try:
                print(f"    🤖 Tentando modelo: {model} (tentativa {attempt + 1})")
                
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        {'parts': [
                            {'text': prompt},
                            {'file_data': {'file_uri': file_uri}}
                        ]}
                    ]
                )
                
                response_text = response.candidates[0].content.parts[0].text
                
                # Tentar extrair JSON da resposta
                if '```json' in response_text:
                    json_text = response_text.split('```json')[1].split('```')[0].strip()
                else:
                    json_text = response_text.strip()
                
                result = json.loads(json_text)
                print(f"    ✅ Sucesso com modelo: {model}")
                return result
                
            except Exception as e:
                is_retryable, error_code = is_retryable_error(e)
                print(f"    ❌ Modelo {model} tentativa {attempt + 1} falhou: {e}")
                
                if error_code == 503:
                    model_stats[model]['last_503'] = time.time()
                    model_stats[model]['failures'] += 1
                    print(f"    🚫 Modelo {model} sobrecarregado - tentando próximo")
                    break  # Pular para próximo modelo
                
                if not is_retryable:
                    break  # Pular para próximo modelo
                
                if attempt < 2:
                    wait_time = RETRY_DELAY * (attempt + 1)
                    time.sleep(wait_time)
    
    # Se chegou aqui, todos os modelos falharam
    print(f"    ⚠️ Todos os modelos falharam na identificação de personas")
    # Fallback: criar personas genéricas
    return {
            "personas": [
                {
                    "id": "Pessoa1",
                    "nome": "Primeira pessoa",
                    "caracteristicas": "Voz principal",
                    "papel": "Participante"
                },
                {
                    "id": "Pessoa2", 
                    "nome": "Segunda pessoa",
                    "caracteristicas": "Voz secundária",
                    "papel": "Participante"
                }
            ]
        }

def transcribe_audio_with_personas(audio_file, personas_info):
    """Transcreve um arquivo de áudio identificando cada persona"""
    print(f"    📝 Transcrevendo {os.path.basename(audio_file)}...")
    
    file_uri = upload_audio_file(audio_file)
    
    personas_list = "\n".join([
        f"- {p['id']}: {p['caracteristicas']}"
        for p in personas_info['personas']
    ])
    
    prompt = f"""
Transcreva este áudio de forma COMPLETAMENTE FIEL, identificando cada fala por persona.

PERSONAS IDENTIFICADAS:
{personas_list}

INSTRUÇÕES CRÍTICAS:
1. Transcreva EXATAMENTE o que é falado, sem omitir, resumir ou parafrasear
2. Identifique cada fala com a persona correspondente
3. Mantenha a ordem cronológica exata das falas
4. NÃO adicione comentários, interpretações ou textos complementares
5. Inclua pausas significativas, hesitações (eh, ah, hm) se presentes
6. Se não conseguir identificar claramente quem está falando, use "Não identificado"

FORMATO DA RESPOSTA:
[PERSONA]: Transcrição exata da fala

[PERSONA]: Transcrição exata da próxima fala

Seja absolutamente fiel ao áudio. Transcreva tudo que for dito.
"""
    
    # Tentar com múltiplos modelos e estratégias
    prompts = [
        prompt,  # Prompt original detalhado
        f"Transcreva este áudio identificando falantes como [Pessoa1], [Pessoa2].\n\nPERSONAS:\n{personas_list}\n\nTranscreva exatamente o que é falado.",
        "Faça a transcrição completa deste áudio identificando diferentes falantes como [Pessoa1], [Pessoa2].",
        "Transcreva este áudio completamente."
    ]
    
    for strategy_idx, current_prompt in enumerate(prompts, 1):
        print(f"    📝 Estratégia {strategy_idx}/{len(prompts)}")
        
        for model in GEMINI_MODELS:
            # Verificar se modelo está disponível
            if time.time() - model_stats[model]['last_503'] < 600:  # 10 min cooldown
                continue
            
            for attempt in range(3):  # 3 tentativas por modelo
                try:
                    print(f"      🤖 Modelo: {model} (tentativa {attempt + 1})")
                    
                    response = client.models.generate_content(
                        model=model,
                        contents=[
                            {'parts': [
                                {'text': current_prompt},
                                {'file_data': {'file_uri': file_uri}}
                            ]}
                        ]
                    )
                    
                    transcription = response.candidates[0].content.parts[0].text
                    
                    if len(transcription.strip()) < 10:
                        raise Exception("Transcrição muito curta")
                    
                    print(f"      ✅ SUCESSO com {model}! ({len(transcription)} chars)")
                    return transcription
                    
                except Exception as e:
                    is_retryable, error_code = is_retryable_error(e)
                    print(f"      ❌ {model} falhou: {e}")
                    
                    if error_code == 503:
                        model_stats[model]['last_503'] = time.time()
                        model_stats[model]['failures'] += 1
                        print(f"      🚫 {model} sobrecarregado")
                        break  # Próximo modelo
                    
                    if not is_retryable:
                        break  # Próximo modelo
                    
                    if attempt < 2:
                        wait_time = RETRY_DELAY * (attempt + 1)
                        time.sleep(wait_time)
        
        # Pausa entre estratégias
        if strategy_idx < len(prompts):
            print(f"    🔄 Tentando próxima estratégia em 10s...")
            time.sleep(10)
    
    # Se chegou aqui, tudo falhou
    print(f"    💀 FALHA TOTAL após todas as estratégias para {os.path.basename(audio_file)}")
    return f"[ERRO_CRÍTICO]: Falha total na transcrição de {os.path.basename(audio_file)} após {len(prompts)} estratégias e {len(GEMINI_MODELS)} modelos"

def create_transcription_document(transcriptions, personas_info, output_path):
    """Cria um documento Word com todas as transcrições"""
    print("  📄 Criando documento Word com transcrições...")
    
    doc = Document()
    
    # Título
    title = doc.add_heading('Transcrição Completa do Áudio', 0)
    
    # Seção de Personas
    doc.add_heading('Personas Identificadas', level=1)
    for persona in personas_info['personas']:
        p = doc.add_paragraph()
        p.add_run(f"{persona['id']}: ").bold = True
        p.add_run(f"{persona['nome']}")
        if persona.get('caracteristicas'):
            p.add_run(f" - {persona['caracteristicas']}")
        if persona.get('papel'):
            p.add_run(f" ({persona['papel']})")
    
    doc.add_page_break()
    
    # Transcrições por segmento
    for i, (filename, transcription) in enumerate(transcriptions, 1):
        doc.add_heading(f'Segmento {i:02d} - {filename}', level=1)
        
        # Dividir por falas e formatar
        lines = transcription.strip().split('\n')
        for line in lines:
            if line.strip():
                if line.startswith('[') and ']:' in line:
                    # É uma fala identificada
                    parts = line.split(']:', 1)
                    if len(parts) == 2:
                        persona = parts[0] + ']:'
                        fala = parts[1].strip()
                        
                        p = doc.add_paragraph()
                        p.add_run(persona).bold = True
                        p.add_run(f' {fala}')
                    else:
                        doc.add_paragraph(line)
                else:
                    doc.add_paragraph(line)
        
        if i < len(transcriptions):
            doc.add_paragraph("─" * 50)
    
    doc.save(output_path)
    print(f"  ✅ Documento salvo em: {output_path}")

def transcribe_audio_segments():
    """Transcreve todos os segmentos de áudio"""
    print("\n📝 ETAPA 2: Transcrevendo arquivos de áudio...")
    
    mp3_dir = "mp3"
    transcricao_dir = "trascricao"
    
    # Criar diretório de transcrição se não existir
    os.makedirs(transcricao_dir, exist_ok=True)
    
    # Encontrar todos os arquivos MP3 gerados
    mp3_files = sorted(glob.glob(os.path.join(mp3_dir, "*.mp3")))
    
    if not mp3_files:
        print("❌ Nenhum arquivo MP3 encontrado no diretório mp3/")
        return False
    
    print(f"  Encontrados {len(mp3_files)} arquivos de áudio para transcrever")
    
    try:
        # Etapa 1: Identificar personas no primeiro arquivo
        first_file = mp3_files[0]
        personas_info = identify_personas(first_file)
        
        print("  Personas identificadas:")
        for persona in personas_info['personas']:
            print(f"    - {persona['id']}: {persona['nome']}")
        
        # Etapa 2: Transcrever todos os arquivos
        transcriptions = []
        
        for i, mp3_file in enumerate(mp3_files, 1):
            print(f"\n  Processando arquivo {i}/{len(mp3_files)}")
            transcription = transcribe_audio_with_personas(mp3_file, personas_info)
            filename = os.path.basename(mp3_file)
            transcriptions.append((filename, transcription))
            
            # Pequena pausa entre requests para não sobrecarregar a API
            time.sleep(3)
        
        # Etapa 3: Criar documento Word
        base_name = Path(mp3_files[0]).stem.replace('-01', '')
        output_path = os.path.join(transcricao_dir, f"{base_name}_transcricao_completa.docx")
        
        create_transcription_document(transcriptions, personas_info, output_path)
        
        # Etapa 4: Limpar arquivos temporários MP3
        print("\n🗑️ Removendo arquivos MP3 temporários...")
        for mp3_file in mp3_files:
            try:
                os.remove(mp3_file)
                print(f"  ✅ Removido: {os.path.basename(mp3_file)}")
            except Exception as e:
                print(f"  ⚠️ Erro ao remover {mp3_file}: {e}")
        
        # Remover diretório mp3 se estiver vazio
        try:
            if os.path.exists(mp3_dir) and not os.listdir(mp3_dir):
                os.rmdir(mp3_dir)
                print("  ✅ Diretório mp3/ removido")
        except Exception as e:
            print(f"  ⚠️ Erro ao remover diretório mp3/: {e}")
        
        print(f"\n✅ Transcrição completa finalizada!")
        print(f"📄 Documento salvo em: {output_path}")
        print("🗑️ Arquivos temporários removidos para economizar espaço")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a transcrição: {e}")
        return False

def main():
    """Função principal que executa todo o pipeline"""
    print("🚀 INICIANDO PROCESSAMENTO COMPLETO")
    print("=" * 50)
    
    try:
        # Etapa 1: Processar arquivos de mídia
        if not process_media_files():
            print("\n❌ Falha no processamento de mídia. Abortando.")
            return
        
        print("\n✅ Processamento de mídia concluído!")
        
        # Etapa 2: Transcrever arquivos
        if not transcribe_audio_segments():
            print("\n❌ Falha na transcrição. Verifique os logs acima.")
            return
        
        print("\n🎉 PROCESSAMENTO COMPLETO FINALIZADO COM SUCESSO!")
        print("=" * 50)
        print("✅ Arquivos processados e divididos em segmentos")
        print("✅ Personas identificadas automaticamente")
        print("✅ Transcrição completa gerada em documento Word")
        print("📁 Verifique a pasta 'trascricao/' para o resultado final")
        
    except KeyboardInterrupt:
        print("\n🛑 Processo interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()