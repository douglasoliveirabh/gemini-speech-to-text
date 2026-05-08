#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile


APP_NAME = "GeminiSpeechToText"
PROJECT_DIR = Path(__file__).resolve().parent
BUILD_ROOT = PROJECT_DIR / "build_artifacts"
DIST_DIR = BUILD_ROOT / "dist"
WORK_DIR = BUILD_ROOT / "work"
SPEC_DIR = BUILD_ROOT / "spec"
EXTERNAL_BINARY_DIRNAME = "ffmpeg-bin"


def get_command_environment():
    pyinstaller_config_dir = BUILD_ROOT / "pyinstaller-config"
    pyinstaller_config_dir.mkdir(parents=True, exist_ok=True)

    environment = dict(os.environ)
    environment["PYINSTALLER_CONFIG_DIR"] = str(pyinstaller_config_dir)
    return environment


def get_default_virtualenv_python() -> Optional[Path]:
    if sys.platform.startswith("win"):
        candidate = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = PROJECT_DIR / ".venv" / "bin" / "python"

    if candidate.exists():
        return candidate
    return None


def python_has_module(python_executable: Path, module_name: str) -> bool:
    result = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import importlib.util, sys; "
                f"sys.exit(0 if importlib.util.find_spec('{module_name}') is not None else 1)"
            ),
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_build_python_executable() -> Path:
    candidates = []

    virtualenv_python = get_default_virtualenv_python()
    if virtualenv_python is not None:
        candidates.append(virtualenv_python)

    current_python = Path(sys.executable).resolve()
    if current_python not in candidates:
        candidates.append(current_python)

    required_modules = ("PyInstaller", "google.genai", "docx")
    for candidate in candidates:
        if all(python_has_module(candidate, module_name) for module_name in required_modules):
            return candidate

    raise RuntimeError(
        "Nenhum interpretador Python compativel foi encontrado para o build. "
        "Instale PyInstaller, google-genai e python-docx no ambiente atual ou no .venv do projeto."
    )


def run_command(command):
    subprocess.run(command, check=True, cwd=PROJECT_DIR, env=get_command_environment())


def capture_command(command):
    result = subprocess.run(
        command,
        check=True,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        env=get_command_environment(),
    )
    return result.stdout


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
    build_python = get_build_python_executable()
    command = [
        str(build_python),
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

    if python_has_module(build_python, "whisper"):
        command.extend(
            [
                "--collect-all",
                "whisper",
                "--copy-metadata",
                "openai-whisper",
            ]
        )

    run_command(command)


def get_packaged_app_root() -> Path:
    if sys.platform == "darwin":
        app_path = DIST_DIR / f"{APP_NAME}.app"
        if not app_path.exists():
            raise RuntimeError(f"Aplicativo nao encontrado em {app_path}")
        return app_path / "Contents" / "Frameworks"

    app_dir = DIST_DIR / APP_NAME
    if not app_dir.exists():
        raise RuntimeError(f"Aplicativo nao encontrado em {app_dir}")
    return app_dir


def copy_file_to_directory(source: Path, target_dir: Path) -> Path:
    resolved_source = source.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / resolved_source.name
    shutil.copy2(resolved_source, target_path)
    return target_path


def get_ffmpeg_tool_paths() -> dict[str, Path]:
    paths = {}
    missing = []

    for binary_name in ("ffmpeg", "ffprobe"):
        resolved = shutil.which(binary_name)
        if resolved is None:
            missing.append(binary_name)
            continue
        paths[binary_name] = Path(resolved).resolve()

    if missing:
        raise RuntimeError(
            "FFmpeg obrigatorio para gerar um pacote portatil completo. "
            "Binarios ausentes no PATH: " + ", ".join(missing)
        )

    return paths


def bundle_ffmpeg_runtime():
    tool_paths = get_ffmpeg_tool_paths()
    bundle_root = get_packaged_app_root() / EXTERNAL_BINARY_DIRNAME
    lib_dir = bundle_root / "lib"

    bundled_tools = {
        name: copy_file_to_directory(path, bundle_root)
        for name, path in tool_paths.items()
    }

    if sys.platform == "darwin":
        ensure_command("otool", "Este comando e necessario para empacotar as bibliotecas do FFmpeg no macOS.")
        ensure_command(
            "install_name_tool",
            "Este comando e necessario para reescrever as dependencias dinamicas do FFmpeg no macOS.",
        )
        bundled_libraries = bundle_macos_ffmpeg_libraries(tool_paths.values(), lib_dir)
        rewrite_macos_ffmpeg_references(bundled_tools, bundled_libraries)
    elif sys.platform.startswith("win"):
        bundle_windows_ffmpeg_libraries(tool_paths.values(), bundle_root)
    else:
        ensure_command("ldd", "Este comando e necessario para descobrir as bibliotecas do FFmpeg no Linux.")
        bundle_linux_ffmpeg_libraries(tool_paths.values(), lib_dir)


def is_macos_system_library(library_path: str) -> bool:
    return library_path.startswith("/System/Library/") or library_path.startswith("/usr/lib/")


def parse_macos_library_references(binary_path: Path) -> list[str]:
    output = capture_command(["otool", "-L", str(binary_path)])
    references = []

    for line in output.splitlines()[1:]:
        reference = line.strip().split(" (", 1)[0]
        if reference:
            references.append(reference)

    return references


def bundle_macos_ffmpeg_libraries(tool_paths, lib_dir: Path) -> dict[Path, Path]:
    pending = []
    copied_libraries: dict[Path, Path] = {}

    for tool_path in tool_paths:
        pending.extend(parse_macos_library_references(Path(tool_path)))

    while pending:
        reference = pending.pop()
        if reference.startswith("@") or is_macos_system_library(reference):
            continue

        library_path = Path(reference).resolve()
        if library_path in copied_libraries:
            continue
        if not library_path.exists():
            raise RuntimeError(f"Biblioteca do FFmpeg nao encontrada durante o empacotamento: {reference}")

        copied_libraries[library_path] = copy_file_to_directory(library_path, lib_dir)
        pending.extend(parse_macos_library_references(library_path))

    return copied_libraries


def rewrite_macos_ffmpeg_references(bundled_tools: dict[str, Path], bundled_libraries: dict[Path, Path]):
    bundled_libraries_by_name = {library.name: library for library in bundled_libraries.values()}

    for library_path in bundled_libraries.values():
        run_command(["install_name_tool", "-id", f"@loader_path/{library_path.name}", str(library_path)])

    for tool_path in bundled_tools.values():
        apply_macos_reference_rewrites(
            tool_path,
            bundled_libraries,
            bundled_libraries_by_name,
            executable=True,
        )

    for library_path in bundled_libraries.values():
        apply_macos_reference_rewrites(
            library_path,
            bundled_libraries,
            bundled_libraries_by_name,
            executable=False,
        )


def apply_macos_reference_rewrites(
    target_path: Path,
    bundled_libraries: dict[Path, Path],
    bundled_libraries_by_name: dict[str, Path],
    executable: bool,
):
    changes = []
    seen_references = set()

    for reference in parse_macos_library_references(target_path):
        if reference in seen_references:
            continue
        seen_references.add(reference)

        bundled_reference = None
        if reference.startswith("@"):
            bundled_reference = bundled_libraries_by_name.get(Path(reference).name)
        elif not is_macos_system_library(reference):
            bundled_reference = bundled_libraries.get(Path(reference).resolve())

        if bundled_reference is None:
            continue

        if executable:
            new_reference = f"@executable_path/lib/{bundled_reference.name}"
        else:
            new_reference = f"@loader_path/{bundled_reference.name}"

        changes.extend(["-change", reference, new_reference])

    if changes:
        run_command(["install_name_tool", *changes, str(target_path)])


def is_linux_system_library(library_path: Path) -> bool:
    library_str = str(library_path)
    return (
        library_str.startswith("/lib/")
        or library_str.startswith("/lib64/")
        or library_str.startswith("/usr/lib/")
        or library_str.startswith("/usr/lib64/")
    )


def parse_linux_library_references(binary_path: Path) -> list[Path]:
    output = capture_command(["ldd", str(binary_path)])
    references = []

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if "=>" not in line:
            continue

        dependency_path = line.split("=>", 1)[1].strip().split(" (", 1)[0]
        if dependency_path == "not found":
            raise RuntimeError(f"Dependencia compartilhada nao resolvida para {binary_path}: {line}")
        if dependency_path.startswith("/"):
            references.append(Path(dependency_path).resolve())

    return references


def bundle_linux_ffmpeg_libraries(tool_paths, lib_dir: Path):
    pending = []
    copied_libraries = set()

    for tool_path in tool_paths:
        pending.extend(parse_linux_library_references(Path(tool_path)))

    while pending:
        library_path = pending.pop()
        if is_linux_system_library(library_path) or library_path in copied_libraries:
            continue
        if not library_path.exists():
            raise RuntimeError(f"Biblioteca do FFmpeg nao encontrada durante o empacotamento: {library_path}")

        copied_libraries.add(library_path)
        copy_file_to_directory(library_path, lib_dir)
        pending.extend(parse_linux_library_references(library_path))


def bundle_windows_ffmpeg_libraries(tool_paths, bundle_root: Path):
    copied_dlls = set()

    for tool_path in tool_paths:
        for dll_path in Path(tool_path).resolve().parent.glob("*.dll"):
            if dll_path in copied_dlls:
                continue
            copied_dlls.add(dll_path)
            copy_file_to_directory(dll_path, bundle_root)


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
    bundle_ffmpeg_runtime()

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
