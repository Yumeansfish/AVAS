import subprocess
import sys
import shutil
import platform
import os
from pathlib import Path

def run(cmd: str, *, cwd: Path = None) -> int:
    """
    Run a shell command in bash -lc (or cmd.exe on Windows) and return its exit code.
    """
    system = platform.system()
    if system == 'Windows':
        # Use cmd on Windows
        full = ["cmd", "/C", cmd]
    else:
        full = ["bash", "-lc", cmd]
    try:
        return subprocess.call(full, cwd=cwd)
    except FileNotFoundError as e:
        print(f"Failed to execute command: {full}\nError: {e}", file=sys.stderr)
        return 1

def find_aw_static() -> Path:
    """
    Search common locations for the ActivityWatch server 'static' directory.
    Returns the Path if found, otherwise None.
    """
    def is_aw_server_static(static_path: Path) -> bool:
        return static_path.is_dir() and static_path.name == 'static' and \
               static_path.parent.name.lower() in ('aw_server', 'aw-server')

    home = Path.home()
    system = platform.system()
    roots = []
    if system == 'Darwin':
        roots = [Path("/Applications"), home / "Applications", Path("/opt"), Path("/usr/local")]
    elif system == 'Linux':
        roots = [home, Path("/usr"), Path("/opt"), Path("/usr/local")]
    elif system == 'Windows':
        # Check Program Files and local app data
        prog = os.environ.get('ProgramFiles', 'C:/Program Files')
        prog_x86 = os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')
        local = os.environ.get('LOCALAPPDATA', home)
        roots = [Path(prog) / 'ActivityWatch' / 'aw-server',
                 Path(prog_x86) / 'ActivityWatch' / 'aw-server',
                 Path(local) / 'Programs' / 'activitywatch' / 'aw-server',
                 home]
    else:
        roots = [home]

    for root in roots:
        if not root or not Path(root).exists():
            continue
        try:
            for static_dir in Path(root).rglob('static'):
                if is_aw_server_static(static_dir):
                    return static_dir.resolve()
        except (PermissionError, OSError):
            continue
    return None

def backup_rebuild_copy(dist_dir: Path, static_dir: Path) -> bool:
    """
    Backup the existing static_dir and replace it with dist_dir contents.
    Returns True on success, False on error (restores backup if copy fails).
    """
    backup_dir = static_dir.parent / (static_dir.name + ".backup")
    try:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(static_dir), str(backup_dir))
        shutil.copytree(str(dist_dir), str(static_dir))
        shutil.rmtree(backup_dir)
        print("✅ Frontend deployed successfully.")
        return True
    except Exception as e:
        print(f"❌ Deployment failed: {e}", file=sys.stderr)
        if backup_dir.exists():
            if static_dir.exists():
                shutil.rmtree(static_dir)
            shutil.move(str(backup_dir), str(static_dir))
            print("🔄 Restored original static directory.")
        return False

def restart_activitywatch() -> None:
    """
    Restart ActivityWatch by killing existing processes and starting the server/client.
    """
    system = platform.system()
    if system == 'Windows':
        subprocess.call(["taskkill", "/F", "/IM", "aw-server.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["taskkill", "/F", "/IM", "ActivityWatch.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        prog_local = os.environ.get('LOCALAPPDATA', os.environ.get('ProgramFiles', r'C:\Program Files'))
        aw_server = Path(prog_local) / 'Programs' / 'activitywatch' / 'aw-server.exe'
        if aw_server.exists():
            subprocess.Popen([str(aw_server)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        aw_client = Path(prog_local) / 'Programs' / 'activitywatch' / 'ActivityWatch.exe'
        if aw_client.exists():
            subprocess.Popen([str(aw_client)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("🔁 ActivityWatch (Windows) 已重启。")

    else:
        # Kill any running ActivityWatch processes
        subprocess.call(["pkill", "-f", "activitywatch"], stderr=subprocess.DEVNULL)
        if system == 'Darwin':
            aw_app = Path("/Applications/ActivityWatch.app")
            if aw_app.exists():
                subprocess.Popen(["open", "-a", "ActivityWatch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif system == 'Linux':
            subprocess.Popen(["aw-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("🔁 ActivityWatch restarted.")

def main():
    dist_dir = Path(__file__).parent / "dist"
    if not dist_dir.exists():
        print(f"Error: dist directory not found at {dist_dir}", file=sys.stderr)
        sys.exit(1)

    static_dir = find_aw_static()
    if not static_dir:
        print("Error: Could not locate ActivityWatch static directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Found static directory: {static_dir}")
    if not backup_rebuild_copy(dist_dir, static_dir):
        sys.exit(1)

    restart_activitywatch()
    print("Deployment complete. Visit http://localhost:5600 to verify.")

if __name__ == '__main__':
    main()








