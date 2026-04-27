# Sistema de Transcrição de Áudio/Vídeo

Este projeto automatiza o processo de transcrição de arquivos de áudio e vídeo, utilizando a API do Google Gemini para identificar personas e transcrever conversas de forma fidedigna.

## 🚀 Funcionalidades

- **Processamento automático**: Converte vídeos para áudio e divide em segmentos configuráveis
- **Identificação de personas**: Reconhece automaticamente diferentes falantes
- **Transcrição fidedigna**: Transcreve exatamente o que é falado, mantendo hesitações e pausas
- **Documento formatado**: Gera um documento Word com transcrições organizadas por persona
- **Limpeza automática**: Remove arquivos temporários após o processamento
- **Interface desktop**: Tela nativa em Python para Windows, macOS e Linux

## 📋 Pré-requisitos

- Python 3.9+
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
python3 -m pip install google-genai python-docx
```

3. Configure a chave da API:
```bash
cp .env.example .env
```

4. Edite o arquivo `.env` e adicione sua chave da API do Google Gemini:
```
GEMINI_API_KEY=sua_chave_api_gemini_aqui
```

## 🖥️ Instalação da Interface Desktop

A interface gráfica foi feita com `tkinter` e usa o mesmo pipeline Python do projeto.

### 1. Dependências Python

Instale os pacotes do projeto:

```bash
python3 -m pip install google-genai python-docx
```

**Windows (PowerShell ou Prompt de Comando):**

Se o comando acima não funcionar, use o launcher do Python:

```bash
py -m pip install google-genai python-docx
```

### 2. FFmpeg

O FFmpeg é obrigatório para converter e dividir vídeos/áudios.

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
1. Baixe o FFmpeg pelo site oficial: https://ffmpeg.org/download.html
2. Extraia ou instale o pacote
3. Adicione a pasta `bin` do FFmpeg ao `PATH`
4. Valide com:

```bash
ffmpeg -version
```

### 3. Tkinter

**macOS com Python do Homebrew:**

Se ao executar a interface aparecer erro como `No module named '_tkinter'`, instale:

```bash
brew install tcl-tk python-tk@3.13
```

Valide com:

```bash
python3 -c "import tkinter; print(tkinter.TkVersion)"
```

Se ainda houver erro:

```bash
brew reinstall python@3.13 python-tk@3.13
```

**macOS com Python do Xcode / Apple:**

Evite rodar a interface com o `python3` do Xcode ou com `/usr/bin/python3`. Em algumas combinacoes de macOS e Tk isso pode abortar ao abrir a janela.

Verifique qual Python esta sendo usado:

```bash
which python3
python3 -c "import sys; print(sys.executable)"
```

Se aparecer um caminho dentro de `Xcode.app` ou `/usr/bin/python3`, use o Python oficial do `python.org` ou um Python do Homebrew com Tk compativel.

Exemplo com Python oficial:

```bash
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m pip install google-genai python-docx
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 interface_desktop.py
```

**Ubuntu/Debian:**
```bash
sudo apt install python3-tk
```

**Windows:**
Normalmente o `tkinter` já vem no instalador oficial do Python.

Se o Python ainda não estiver instalado:

1. Baixe o instalador oficial em https://www.python.org/downloads/windows/
2. Durante a instalação, marque a opção **Add Python to PATH**
3. Conclua a instalação

Valide com:

```bash
py -c "import tkinter; print(tkinter.TkVersion)"
```

Se esse comando falhar, reinstale o Python oficial para Windows garantindo que a instalação inclua `tcl/tk and IDLE`.

### 4. Arquivo `.env`

Ao rodar o projeto pelo código-fonte, o arquivo `.env` fica na raiz do projeto.

Crie o arquivo de configuração:

```bash
cp .env.example .env
```

Edite o `.env` e adicione sua chave:

```env
GEMINI_API_KEY=sua_chave_api_gemini_aqui
```

Tambem e possivel configurar a chave diretamente pela interface, usando o campo `GEMINI_API_KEY` e o botao `Salvar no .env`.

### 5. Executar a interface

Depois de instalar tudo:

```bash
python3 interface_desktop.py
```

**Windows:**

```bash
py interface_desktop.py
```

## 📦 Gerar Instalador / Pacote Distribuível

O projeto inclui o script `build_installer.py`, que gera o pacote para o sistema operacional atual.

Importante:
- Execute o build no proprio sistema alvo
- macOS gera `.dmg`
- Windows gera instalador `.exe` se o Inno Setup estiver instalado; caso contrario, gera um `.zip` portatil
- Linux gera um `.tar.gz` portatil

### 1. Instale as dependências de build

macOS / Linux:

```bash
python3 -m pip install pyinstaller google-genai python-docx
```

Windows:

```bash
py -m pip install pyinstaller google-genai python-docx
```

### 2. Dependências opcionais por sistema

**Windows com instalador `.exe`:**

Instale o Inno Setup 6 para que o script gere um instalador nativo:
https://jrsoftware.org/isinfo.php

Sem o Inno Setup, o script ainda gera um `.zip` portatil.

**macOS:**

O script usa `hdiutil`, que ja vem no macOS, para gerar o `.dmg`.

**Linux:**

O script gera um `.tar.gz` com a pasta do aplicativo. Isso evita depender de um formato especifico de distribuicao.

### 3. Executar o build

macOS / Linux:

```bash
python3 build_installer.py
```

Windows:

```bash
py build_installer.py
```

Os artefatos sao gerados em:

```bash
build_artifacts/
```

### 4. Resultado esperado por sistema

**macOS:**
- `build_artifacts/GeminiSpeechToText-macOS.dmg`

**Windows com Inno Setup:**
- `build_artifacts/windows-installer/GeminiSpeechToText-Windows-Installer.exe`

**Windows sem Inno Setup:**
- `build_artifacts/GeminiSpeechToText-Windows-portable.zip`

**Linux:**
- `build_artifacts/GeminiSpeechToText-Linux.tar.gz`

## 📁 Estrutura do Projeto

```
projeto/
├── arquivo/                  # Entrada local ao rodar pelo código-fonte
├── mp3/                      # Diretório temporário para segmentos
├── trascricao/               # Documentos finais de transcrição
├── interface_desktop.py      # Interface gráfica
├── processar_completo.py    # Script principal (pipeline completo)
├── processar_videos.py      # Script para conversão de vídeo para áudio
├── transcrever_audios.py    # Script para transcrição de segmentos
├── build_installer.py       # Script de build por sistema operacional
├── .env             # Suas variáveis de ambiente
├── .env.example     # Modelo de configuração
└── README.md        # Este arquivo
```

Quando o aplicativo e empacotado, os dados deixam de ficar dentro da pasta do projeto e passam a ser salvos na pasta local do usuario:
- macOS: `~/Library/Application Support/GeminiSpeechToText/`
- Linux: `~/.local/share/GeminiSpeechToText/`
- Windows: `%APPDATA%\GeminiSpeechToText\`

## 🎯 Como Usar

### Interface Desktop (Windows/macOS/Linux)

1. Inicie a interface:
```bash
python3 interface_desktop.py
```

No Windows:
```bash
py interface_desktop.py
```

2. Informe sua `GEMINI_API_KEY`
3. Clique em **Salvar no .env**
4. Clique em **Selecionar arquivos** e escolha um ou mais vídeos/áudios
5. Clique em **Gerar transcrição**
6. Acompanhe os logs na própria janela
7. O arquivo final `.docx` será salvo em `trascricao/`

Observações:
- A interface usa o mesmo pipeline do script `processar_completo.py`
- Ao rodar empacotado, os arquivos ficam na pasta local do aplicativo, nao na pasta do projeto
- O FFmpeg continua sendo obrigatório

### Pipeline Completo (Recomendado)

1. Coloque seus arquivos de vídeo ou áudio na pasta `arquivo/`
2. Execute o processamento completo:
```bash
python3 processar_completo.py
```

No Windows:
```bash
py processar_completo.py
```

Este script irá:
- Converter vídeos para MP3 (se necessário)
- Dividir arquivos longos em segmentos configuráveis via `.env`
- Identificar personas automaticamente
- Transcrever todos os segmentos
- Gerar documento Word formatado
- Limpar arquivos temporários

### Scripts Individuais

**Apenas conversão de vídeo:**
```bash
python3 processar_videos.py
```

**Apenas transcrição (com segmentos já prontos):**
```bash
python3 transcrever_audios.py
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
- O arquivo final é salvo na pasta `trascricao/`

## ⚠️ Limitações

- Arquivos são divididos conforme `SEGMENT_DURATION_MINUTES` no `.env` (padrão: 15 minutos)
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

**Erro de Tkinter no macOS:**
- Se aparecer `No module named '_tkinter'`, instale `tcl-tk` e `python-tk@3.13`
- Depois valide com `python3 -c "import tkinter; print(tkinter.TkVersion)"`
- Se a interface abortar ao abrir a janela, verifique se voce esta usando o Python do Xcode ou `/usr/bin/python3`
- Prefira o Python oficial do `python.org` ou um Python do Homebrew com Tk compativel

**Build do instalador falhou:**
- Verifique se `pyinstaller` foi instalado no mesmo Python usado no build
- No Windows, instale o Inno Setup se quiser um instalador `.exe`
- No macOS, gere o `.dmg` em um Mac
- No Linux, gere o `.tar.gz` em uma maquina Linux

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
