#!/usr/bin/env python3
import argparse
import importlib.util
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


APP_NAME = "GeminiSpeechToText"
PROJECT_DIR = Path(__file__).resolve().parent
BUILD_ROOT = PROJECT_DIR / "build_artifacts"
DIST_DIR = BUILD_ROOT / "dist"
WORK_DIR = BUILD_ROOT / "work"
SPEC_DIR = BUILD_ROOT / "spec"


def run_command(command):
    subprocess.run(command, check=True, cwd=PROJECT_DIR)


def ensure_command(command_name, install_hint):
    if shutil.which(command_name):
        return
    raise RuntimeError(f"Comando obrigatorio nao encontrado: {command_name}. {install_hint}")


def clean_build_directories():
    if BUILD_ROOT.exists():
        shutil.rmtree(BUILD_ROOT)

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)


def build_with_pyinstaller():
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(WORK_DIR),
        "--specpath",
        str(SPEC_DIR),
        "--collect-all",
        "google.genai",
        "--collect-all",
        "docx",
        "--copy-metadata",
        "google-genai",
        "--copy-metadata",
        "python-docx",
        "interface_desktop.py",
    ]

    if importlib.util.find_spec("whisper") is not None:
        command.extend(
            [
                "--collect-all",
                "whisper",
                "--copy-metadata",
                "openai-whisper",
            ]
        )

    run_command(command)


def build_macos_dmg():
    ensure_command("hdiutil", "Este comando so funciona no macOS.")

    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        raise RuntimeError(f"Aplicativo nao encontrado em {app_path}")

    dmg_path = BUILD_ROOT / f"{APP_NAME}-macOS.dmg"
    staging_dir = Path(tempfile.mkdtemp(prefix="gemini-stt-dmg-"))

    try:
        shutil.copytree(app_path, staging_dir / app_path.name)
        command = [
            "hdiutil",
            "create",
            "-volname",
            APP_NAME,
            "-srcfolder",
            str(staging_dir),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ]
        run_command(command)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    return dmg_path


def build_windows_package():
    app_dir = DIST_DIR / APP_NAME
    if not app_dir.exists():
        raise RuntimeError(f"Aplicativo nao encontrado em {app_dir}")

    installer_path = try_build_inno_setup_installer(app_dir)
    if installer_path is not None:
        return installer_path

    zip_path = BUILD_ROOT / f"{APP_NAME}-Windows-portable.zip"
    create_zip_archive(app_dir, zip_path)
    return zip_path


def try_build_inno_setup_installer(app_dir: Path):
    iscc_path = find_inno_setup_compiler()
    if iscc_path is None:
        return None

    iss_path = BUILD_ROOT / "windows-installer.iss"
    installer_output_dir = BUILD_ROOT / "windows-installer"
    installer_output_dir.mkdir(parents=True, exist_ok=True)

    script = f"""
[Setup]
AppName={APP_NAME}
AppVersion=1.0.0
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir={installer_output_dir}
OutputBaseFilename={APP_NAME}-Windows-Installer
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "{app_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{autodesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos adicionais:"
"""
    iss_path.write_text(script.strip() + "\n", encoding="utf-8")
    run_command([str(iscc_path), str(iss_path)])

    installers = sorted(installer_output_dir.glob("*.exe"))
    if not installers:
        raise RuntimeError("O Inno Setup foi executado, mas nenhum instalador .exe foi gerado.")

    return installers[0]


def find_inno_setup_compiler():
    direct_match = shutil.which("iscc")
    if direct_match:
        return Path(direct_match)

    candidate_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]

    for candidate in candidate_paths:
        if candidate.exists():
            return candidate

    return None


def build_linux_package():
    app_dir = DIST_DIR / APP_NAME
    if not app_dir.exists():
        raise RuntimeError(f"Aplicativo nao encontrado em {app_dir}")

    tar_path = BUILD_ROOT / f"{APP_NAME}-Linux.tar.gz"
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(app_dir, arcname=APP_NAME)
    return tar_path


def create_zip_archive(source_dir: Path, target_zip: Path):
    with ZipFile(target_zip, "w", ZIP_DEFLATED) as archive:
        for file_path in source_dir.rglob("*"):
            archive.write(file_path, file_path.relative_to(source_dir.parent))


def main():
    parser = argparse.ArgumentParser(
        description="Gera o pacote distribuivel do aplicativo para o sistema operacional atual."
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Nao remove a pasta build_artifacts antes de iniciar o build.",
    )
    args = parser.parse_args()

    if not args.no_clean:
        clean_build_directories()
    else:
        BUILD_ROOT.mkdir(parents=True, exist_ok=True)
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        WORK_DIR.mkdir(parents=True, exist_ok=True)
        SPEC_DIR.mkdir(parents=True, exist_ok=True)

    build_with_pyinstaller()

    if sys.platform == "darwin":
        artifact = build_macos_dmg()
    elif sys.platform.startswith("win"):
        artifact = build_windows_package()
    else:
        artifact = build_linux_package()

    print(f"Pacote gerado com sucesso: {artifact}")
    print("Execute este script no proprio sistema operacional alvo para gerar o pacote correto.")


if __name__ == "__main__":
    main()
