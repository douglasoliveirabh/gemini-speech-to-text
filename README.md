# Sistema de Transcrição de Áudio/Vídeo

Este projeto automatiza o processo de transcrição de arquivos de áudio e vídeo, permitindo usar a API do Google Gemini ou o Whisper local para gerar transcrições.

## 🚀 Funcionalidades

- **Processamento automático**: Converte vídeos para áudio e divide em segmentos configuráveis
- **Dois modos de transcrição**: Gemini API ou Whisper local
- **Identificação de personas**: Disponível no modo Gemini
- **Transcrição local**: Whisper roda sem depender da API do Gemini
- **Documento formatado**: Gera um documento Word com o resultado final
- **Limpeza automática**: Remove arquivos temporários após o processamento
- **Interface desktop**: Tela nativa em Python para Windows, macOS e Linux

## 📋 Pré-requisitos

- Python 3.9+
- FFmpeg (para processamento de áudio/vídeo)
- Chave da API do Google Gemini para o modo Gemini

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
python3 -m pip install google-genai python-docx openai-whisper
```

3. Configure a chave da API:
```bash
cp .env.example .env
```

4. Edite o arquivo `.env` de acordo com o modo desejado:
```env
TRANSCRIPTION_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_api_gemini_aqui
WHISPER_MODEL=base
WHISPER_LANGUAGE=
```

## 🖥️ Instalação da Interface Desktop

A interface gráfica foi feita com `tkinter` e usa o mesmo pipeline Python do projeto.

### 1. Dependências Python

Instale os pacotes do projeto:

```bash
python3 -m pip install google-genai python-docx openai-whisper
```

**Windows (PowerShell ou Prompt de Comando):**

Se o comando acima não funcionar, use o launcher do Python:

```bash
py -m pip install google-genai python-docx openai-whisper
```

Observações:
- `openai-whisper` so e usado quando o provedor selecionado for `Whisper local`
- Na primeira execucao do Whisper, o modelo escolhido sera baixado automaticamente

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

Edite o `.env` com o modo desejado:

```env
TRANSCRIPTION_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_api_gemini_aqui
WHISPER_MODEL=base
WHISPER_LANGUAGE=
```

Opcoes:
- `TRANSCRIPTION_PROVIDER=gemini` usa a API do Gemini
- `TRANSCRIPTION_PROVIDER=whisper_local` usa Whisper local
- `WHISPER_MODEL` pode ser `tiny`, `base`, `small`, `medium`, `large` ou `turbo`
- `WHISPER_LANGUAGE` pode ficar vazio para deteccao automatica ou receber algo como `pt`, `en`, `es` ou `pt-BR` (normalizado para `pt`)

Tambem e possivel configurar tudo diretamente pela interface.

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

### Como criar o instalador

1. Entre na pasta do projeto
2. Instale as dependencias de build
3. Execute o script `build_installer.py`
4. Abra a pasta `build_artifacts/` para pegar o arquivo gerado

Exemplo no macOS / Linux:

```bash
cd /caminho/do/projeto
python3 -m pip install pyinstaller google-genai python-docx openai-whisper
brew install ffmpeg
python3 build_installer.py
```

Exemplo no Windows:

```bash
cd C:\caminho\do\projeto
py -m pip install pyinstaller google-genai python-docx openai-whisper
py build_installer.py
```

### 1. Instale as dependências de build

macOS / Linux:

```bash
python3 -m pip install pyinstaller google-genai python-docx openai-whisper
```

Windows:

```bash
py -m pip install pyinstaller google-genai python-docx openai-whisper
```

### 2. Dependências opcionais por sistema

**Windows com instalador `.exe`:**

Instale o Inno Setup 6 para que o script gere um instalador nativo:
https://jrsoftware.org/isinfo.php

Sem o Inno Setup, o script ainda gera um `.zip` portatil.

**macOS:**

O script usa `hdiutil`, que ja vem no macOS, para gerar o `.dmg`.
O FFmpeg precisa estar instalado na maquina de build para que `ffmpeg`, `ffprobe` e as bibliotecas dinamicas deles sejam incluidos dentro do `.app`.

**Linux:**

O script gera um `.tar.gz` com a pasta do aplicativo. Isso evita depender de um formato especifico de distribuicao.
O FFmpeg precisa estar instalado na maquina de build para que os binarios sejam copiados para o pacote final.

### 3. Executar o build

macOS / Linux:

```bash
python3 build_installer.py
```

Windows:

```bash
py build_installer.py
```

Opcao util:

- `py build_installer.py --no-clean` ou `python3 build_installer.py --no-clean`: reaproveita a pasta `build_artifacts/` sem limpar tudo antes

Os artefatos sao gerados em:

```bash
build_artifacts/
```

### 4. Resultado esperado por sistema

**macOS:**
- `build_artifacts/GeminiSpeechToText-macOS.dmg`
- Resultado: imagem `.dmg` para distribuir ou instalar no proprio macOS

**Windows com Inno Setup:**
- `build_artifacts/windows-installer/GeminiSpeechToText-Windows-Installer.exe`
- Resultado: instalador `.exe` tradicional com assistente de instalacao

**Windows sem Inno Setup:**
- `build_artifacts/GeminiSpeechToText-Windows-portable.zip`
- Resultado: pacote portatil compactado, sem instalador

**Linux:**
- `build_artifacts/GeminiSpeechToText-Linux.tar.gz`
- Resultado: pacote portatil compactado

### Observacoes sobre o build

- O instalador e gerado a partir da interface grafica `interface_desktop.py`
- O build usa `PyInstaller` em todos os sistemas
- Se `openai-whisper` estiver instalado no ambiente, ele tambem sera incluido no pacote
- O build agora empacota `ffmpeg` e `ffprobe` junto com o executavel gerado
- No macOS, o script tambem copia as bibliotecas dinamicas usadas pelo FFmpeg para o `.app`
- No Windows, o `.exe` so e gerado se o compilador do Inno Setup (`ISCC.exe`) estiver disponivel
- Execute o build no sistema de destino: macOS gera pacote de macOS, Windows gera pacote de Windows, Linux gera pacote de Linux

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

### Executar em modo tela

O modo tela e a execucao da interface grafica do projeto, em vez do processamento direto pelo terminal.

1. Entre na pasta do projeto
2. Execute a interface grafica:

```bash
cd /caminho/do/projeto
python3 interface_desktop.py
```

No Windows:
```bash
cd C:\caminho\do\projeto
py interface_desktop.py
```

Se voce estiver usando o aplicativo empacotado pelo `build_installer.py`, basta abrir o executavel gerado para o seu sistema. Nesse caso, nao e necessario rodar `interface_desktop.py` manualmente.

Quando a interface abrir, o uso passa a ser todo pela tela: voce escolhe o provedor, adiciona os arquivos, acompanha os logs e abre a pasta das transcricoes pelos botoes da propria janela.

### Como usar a tela

Ao abrir a janela, a interface e dividida em 4 areas principais:

- **Configuracao da transcricao**: escolha entre `Gemini API` e `Whisper local`
- **Barra de acoes**: adiciona arquivos, atualiza a lista e abre as pastas do app
- **Arquivos prontos para processar**: mostra a fila atual de videos e audios copiados para o app
- **Logs do processamento**: exibe cada etapa da conversao, segmentacao e transcricao

### Fluxo recomendado na interface

1. Em **Provedor**, escolha `Gemini API` ou `Whisper local`
2. Se escolher `Gemini API`, preencha `GEMINI_API_KEY`
3. Se escolher `Whisper local`, selecione `WHISPER_MODEL` e, se quiser, informe `WHISPER_LANGUAGE`
4. Clique em **Salvar configuracoes**
5. Clique em **Selecionar arquivos** para escolher um ou mais videos/audios do computador
6. Confira os arquivos na lista **Arquivos prontos para processar**
7. Clique em **Gerar transcricao**
8. Acompanhe o andamento em **Logs do processamento**
9. Ao final, abra a pasta de saida pelo botao **Abrir transcricoes**

### O que cada campo faz

- `Gemini API`: usa a API do Google Gemini e tenta identificar diferentes falantes
- `Whisper local`: roda a transcricao localmente, sem API externa
- `GEMINI_API_KEY`: chave obrigatoria quando o provedor for Gemini
- `WHISPER_MODEL`: define o tamanho do modelo local (`tiny`, `base`, `small`, `medium`, `large`, `turbo`)
- `WHISPER_LANGUAGE`: pode ficar vazio para autodeteccao, ou receber valores como `pt`, `en` ou `es`

### O que cada botao faz

- **Selecionar arquivos**: copia os arquivos escolhidos para a pasta de entrada do aplicativo
- **Atualizar lista**: recarrega manualmente a fila de arquivos exibida na tela
- **Abrir pasta de entrada**: abre a pasta onde os arquivos aguardam processamento
- **Abrir transcricoes**: abre a pasta onde os `.docx` finais sao gravados
- **Abrir pasta do app**: abre a pasta base do aplicativo, onde tambem fica o `.env`
- **Gerar transcricao**: inicia o pipeline completo com os arquivos listados

### Comportamento importante da tela

- Os arquivos selecionados sao **copiados** para a pasta do aplicativo; o arquivo original nao e movido
- Nomes com acentos ou caracteres especiais podem ser normalizados automaticamente para evitar erros
- Se ja existir um arquivo com o mesmo nome, a interface cria um nome unico
- Durante o processamento, os campos e botoes de configuracao ficam desabilitados
- Ao fechar a janela com uma transcricao em andamento, a interface pergunta se deve cancelar o processamento
- O documento final e salvo como `.docx` na pasta `trascricao/` ou na pasta local do app empacotado

Observações:
- A interface usa o mesmo pipeline do script `processar_completo.py`
- Ao rodar empacotado, os arquivos ficam na pasta local do aplicativo, nao na pasta do projeto
- O FFmpeg continua sendo obrigatório
- O modo Whisper local nao identifica automaticamente diferentes falantes neste fluxo atual

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

No modo Gemini, o sistema analisa automaticamente o primeiro segmento de áudio para:
- Identificar quantas pessoas falam
- Caracterizar cada voz (tom, velocidade, etc.)
- Determinar o papel de cada pessoa na conversa

## 📄 Saída

O sistema gera um documento Word (`.docx`) contendo:
- Lista de personas identificadas no modo Gemini
- Transcrição completa dividida por segmentos
- Identificação de quem fala em cada momento no modo Gemini
- Timestamps por trecho no modo Whisper local
- Formatação clara e organizizada
- O arquivo final é salvo na pasta `trascricao/`

## ⚠️ Limitações

- Arquivos são divididos conforme `SEGMENT_DURATION_MINUTES` no `.env` (padrão: 15 minutos)
- O modo Gemini requer conexão com internet e quota disponível na API
- O modo Whisper local pode ser mais lento e baixa o modelo na primeira execução
- Qualidade da identificação de personas depende da clareza do áudio
- Suporte limitado a idiomas (principalmente português)

## 🔧 Solução de Problemas

**Erro de API:**
- Verifique se sua chave do Gemini está correta no arquivo `.env`
- Confirme se você tem créditos disponíveis na API

**Erro do Whisper local:**
- Verifique se `openai-whisper` foi instalado no mesmo ambiente Python da interface
- Na primeira execucao, aguarde o download do modelo
- Se o processamento local estiver muito lento, troque `WHISPER_MODEL` para `tiny` ou `base`
- Se aparecer `Numpy is not available`, reinstale uma versao compativel no mesmo ambiente: `python3 -m pip install "numpy<2" --force-reinstall`

**Erro do FFmpeg:**
- Ao rodar pelo codigo-fonte, certifique-se de que o FFmpeg esta instalado e no PATH
- Ao gerar um pacote distribuivel, instale o FFmpeg antes do `build_installer.py`
- Teste executando `ffmpeg -version` e `ffprobe -version` no terminal da maquina de build

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
