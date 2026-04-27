#!/usr/bin/env python3
from processar_completo import (
    PipelineContext,
    ProcessingCancelled,
    ensure_external_dependencies,
    transcribe_audio_segments,
)


def main():
    try:
        ensure_external_dependencies()
        context = PipelineContext()
        transcribe_audio_segments(context)
    except ProcessingCancelled as error:
        print(f"Processamento interrompido: {error}")
    except KeyboardInterrupt:
        print("Processamento interrompido pelo usuario.")
    except Exception as error:
        print(f"Erro fatal: {error}")
        raise


if __name__ == "__main__":
    main()
