# Sistema de Transcrição de Áudio/Vídeo

Este projeto automatiza o processo de transcrição de arquivos de áudio e vídeo, utilizando a API do Google Gemini para identificar personas e transcrever conversas de forma fidedigna.

## 🚀 Funcionalidades

- **Processamento automático**: Converte vídeos para áudio e divide em segmentos de 30 minutos
- **Identificação de personas**: Reconhece automaticamente diferentes falantes
- **Transcrição fidedigna**: Transcreve exatamente o que é falado, mantendo hesitações e pausas
- **Documento formatado**: Gera um documento Word com transcrições organizadas por persona
- **Limpeza automática**: Remove arquivos temporários após o processamento

## 📋 Pré-requisitos

- Python 3.7+
- FFmpeg (para processamento de áudio/vídeo)
- Chave da API do Google Gemini

### Instalação do FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Baixe do site oficial: https://ffmpeg.org/download.html

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd trascricao-quebra-video-trascricao
```

2. Instale as dependências Python:
```bash
pip install google-genai python-docx python-dotenv
```

3. Configure a chave da API:
```bash
cp .env.example .env
```

4. Edite o arquivo `.env` e adicione sua chave da API do Google Gemini:
```
GEMINI_API_KEY=sua_chave_api_gemini_aqui
```

## 📁 Estrutura do Projeto

```
projeto/
├── arquivo/          # Coloque seus arquivos de vídeo/áudio aqui
├── mp3/             # Diretório temporário para segmentos (criado automaticamente)
├── trascricao/      # Documentos finais de transcrição
├── processar_completo.py    # Script principal (pipeline completo)
├── processar_videos.py      # Script para conversão de vídeo para áudio
├── transcrever_audios.py    # Script para transcrição de segmentos
├── .env             # Suas variáveis de ambiente
├── .env.example     # Modelo de configuração
└── README.md        # Este arquivo
```

## 🎯 Como Usar

### Pipeline Completo (Recomendado)

1. Coloque seus arquivos de vídeo ou áudio na pasta `arquivo/`
2. Execute o processamento completo:
```bash
python processar_completo.py
```

Este script irá:
- Converter vídeos para MP3 (se necessário)
- Dividir arquivos longos em segmentos de 30 minutos
- Identificar personas automaticamente
- Transcrever todos os segmentos
- Gerar documento Word formatado
- Limpar arquivos temporários

### Scripts Individuais

**Apenas conversão de vídeo:**
```bash
python processar_videos.py
```

**Apenas transcrição (com segmentos já prontos):**
```bash
python transcrever_audios.py
```

## 📝 Formatos Suportados

**Vídeo:** .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm, .m4v, .3gp, .ogv
**Áudio:** .mp3, .wav, .m4a, .aac, .flac, .ogg

## 🎭 Identificação de Personas

O sistema analisa automaticamente o primeiro segmento de áudio para:
- Identificar quantas pessoas falam
- Caracterizar cada voz (tom, velocidade, etc.)
- Determinar o papel de cada pessoa na conversa

## 📄 Saída

O sistema gera um documento Word (`.docx`) contendo:
- Lista de personas identificadas
- Transcrição completa dividida por segmentos
- Identificação de quem fala em cada momento
- Formatação clara e organizizada

## ⚠️ Limitações

- Arquivos são divididos em segmentos de 30 minutos (limitação da API)
- Requer conexão com internet para usar a API do Gemini
- Qualidade da identificação de personas depende da clareza do áudio
- Suporte limitado a idiomas (principalmente português)

## 🔧 Solução de Problemas

**Erro de API:**
- Verifique se sua chave do Gemini está correta no arquivo `.env`
- Confirme se você tem créditos disponíveis na API

**Erro do FFmpeg:**
- Certifique-se de que o FFmpeg está instalado e no PATH
- Teste executando `ffmpeg -version` no terminal

**Problemas de qualidade:**
- Use arquivos com áudio claro e bem definido
- Evite muito ruído de fundo
- Certifique-se de que as vozes estão bem separadas

## 📊 Monitoramento

O sistema fornece logs detalhados durante a execução:
- ✅ Operações bem-sucedidas
- ⚠️ Avisos e problemas menores
- ❌ Erros que impedem a continuação
- 📊 Progresso de cada etapa

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Se encontrar problemas ou tiver dúvidas:
1. Verifique a seção de solução de problemas
2. Consulte os logs do sistema para detalhes do erro
3. Abra uma issue no repositório com detalhes do problema