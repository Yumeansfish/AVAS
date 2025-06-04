import subprocess
import sys
import shutil
import platform
from pathlib import Path
import os

def run(cmd: str, *, cwd: Path = None) -> int:
    full = ["bash", "-lc", cmd]
    try:
        return subprocess.call(full, cwd=cwd)
    except FileNotFoundError as e:
        print(f"Failed to execute command: {full}\nError: {e}", file=sys.stderr)
        return 1

def ensure_wget() -> None:
    if shutil.which("wget"):
        return

    print(">>> Wget not found. Installing wget...")
    system = platform.system()
    if system == "Darwin":
        if shutil.which("brew"):
            print(">>> macOS: Installing wget via Homebrew...")
            if run("brew install wget") != 0:
                print("Failed to install wget. Please check Homebrew installation.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: Homebrew not found on macOS. Please install Homebrew first.", file=sys.stderr)
            sys.exit(1)

    elif system == "Linux":
        if shutil.which("apt-get"):
            print(">>> Linux (apt-get): Installing wget...")
            if run("sudo apt-get update && sudo apt-get install -y wget") != 0:
                print("Failed to install wget via apt-get.", file=sys.stderr)
                sys.exit(1)
        elif shutil.which("yum"):
            print(">>> Linux (yum): Installing wget...")
            if run("sudo yum install -y wget") != 0:
                print("Failed to install wget via yum.", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: Neither apt-get nor yum found. Please install wget manually.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: Unknown system type ({system}). Please install wget manually.", file=sys.stderr)
        sys.exit(1)

def find_aw_static() -> Path:
    print(">>> Searching for ActivityWatch static directory...")
    
    def is_aw_server_static(static_path: Path) -> bool:
        if not static_path.is_dir() or static_path.name != "static":
            return False
        
        parent = static_path.parent
        parent_name = parent.name.lower()
        
        if parent_name in ['aw_server', 'aw-server']:
            return True
        
        path_str = str(static_path).lower()
        if 'activitywatch' in path_str and ('aw_server' in path_str or 'aw-server' in path_str):
            return True
            
        return False
    
    search_roots = []
    home = Path.home()
    system = platform.system()
    
    if system == "Darwin":
        search_roots = ["/Applications", home / "Applications", "/opt", "/usr/local"]
    elif system == "Linux":
        search_roots = [home, "/usr", "/opt", "/usr/local"]
    else:
        search_roots = [home]
    
    print(">>> Searching common locations for static directory...")
    
    for root in search_roots:
        if not Path(root).exists():
            continue
            
        print(f"    Searching {root}...")
        
        try:
            for static_path in Path(root).rglob("static"):
                if is_aw_server_static(static_path):
                    print(f"    Found matching static directory: {static_path}")
                    return static_path.resolve()
        except (PermissionError, OSError) as e:
            continue
    
    print(">>> ActivityWatch static directory not found")
    return None

def backup_rebuild_copy(dist_dir: Path, static_dir: Path) -> bool:
    print(f">>> Using backup-rebuild method to copy {dist_dir} to {static_dir}...")
    
    backup_dir = static_dir.parent / f"{static_dir.name}.backup"
    
    try:
        print(f">>> Backing up original directory to {backup_dir}...")
        backup_cmd = f"sudo mv {static_dir} {backup_dir}"
        if run(backup_cmd) != 0:
            print("❌ Failed to backup original directory")
            return False
        
        print(f">>> Copying new content to {static_dir}...")
        copy_cmd = f"sudo cp -r {dist_dir} {static_dir}"
        if run(copy_cmd) != 0:
            print("❌ Failed to copy new content, attempting to restore backup...")
            restore_cmd = f"sudo mv {backup_dir} {static_dir}"
            run(restore_cmd)
            return False
        
        print(f">>> Removing backup directory {backup_dir}...")
        cleanup_cmd = f"sudo rm -rf {backup_dir}"
        if run(cleanup_cmd) != 0:
            print("⚠️  Failed to remove backup, but copy succeeded. You can manually delete:")
            print(f"   sudo rm -rf {backup_dir}")
        
        print("succeeded!")
        return True
        
    except Exception as e:
        print(f"Error during backup-rebuild process: {e}")
        if backup_dir.exists():
            print(">>> Attempting to restore backup...")
            restore_cmd = f"sudo mv {backup_dir} {static_dir}"
            run(restore_cmd)
        return False

def main():
    print("\n=== Step 1: Clone or pull aw-webui repository to ~/aw-webui ===")
    awui_dir = (Path.home() / "aw-webui").expanduser().resolve()

    if awui_dir.exists() and (awui_dir / ".git").exists():
        print(f">>> Directory exists and is a Git repository, executing git pull: {awui_dir}")
        if run("git pull", cwd=awui_dir) != 0:
            print("git pull failed. Please check network or repository status.", file=sys.stderr)
            sys.exit(1)
    else:
        if awui_dir.exists():
            print(f">>> Found {awui_dir} exists but is not a Git repository, removing old directory.")
            try:
                shutil.rmtree(str(awui_dir))
            except Exception as e:
                print(f"Failed to remove old directory: {e}", file=sys.stderr)
                sys.exit(1)

        print(f">>> Cloning aw-webui repository to {awui_dir}...")
        try:
            ret = subprocess.call([
                "git", "clone",
                "https://github.com/Yumeansfish/aw-webui.git",
                str(awui_dir)
            ])
        except FileNotFoundError:
            print("Error: git executable not found. Please install git.", file=sys.stderr)
            sys.exit(1)

        if ret != 0:
            print("git clone aw-webui failed. Please check network or repository address.", file=sys.stderr)
            sys.exit(1)

    print("\n=== Step 2: Install nvm (requires wget), Node 23.11.0 and build aw-webui ===")

    ensure_wget()

    print(">>> Installing/updating nvm via wget...")
    install_nvm_cmd = "wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash"
    if run(install_nvm_cmd) != 0:
        print("nvm installation script failed. Please check network connection or permissions.", file=sys.stderr)
        sys.exit(1)

    print(">>> Installing and switching to Node.js 23.11.0 via nvm...")
    nvm_init = 'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"'
    node_cmd = f'{nvm_init} && nvm install 23.11.0 && nvm use 23.11.0'
    if run(node_cmd) != 0:
        print("Node installation or switching failed. Please ensure nvm is properly loaded.", file=sys.stderr)
        sys.exit(1)

    print(f">>> Entering {awui_dir}, executing npm install && npm run build...")
    build_cmd = f"cd {str(awui_dir)} && npm install && npm run build"
    if run(build_cmd) != 0:
        print("npm install or npm run build failed. Please check frontend dependencies.", file=sys.stderr)
        sys.exit(1)

    print("\n=== Step 3: Search aw-server/static directory and copy frontend static files ===")
    aw_static_path = find_aw_static()
    
    if not aw_static_path:
        print("\nError: Could not automatically find aw-server/static directory.", file=sys.stderr)
        manual_path = input("\nPlease enter the full path to the static directory: ").strip()
        if not manual_path:
            sys.exit(1)
        
        aw_static_path = Path(manual_path)
        if not aw_static_path.is_dir():
            print(f"Error: Specified path does not exist or is not a directory: {aw_static_path}", file=sys.stderr)
            sys.exit(1)

    print(f">>> Found ActivityWatch static directory: {aw_static_path}")
    dist_dir = awui_dir / "dist"
    if not dist_dir.exists():
        print(f"Error: dist directory not found in {awui_dir}, indicating frontend build failed.", file=sys.stderr)
        sys.exit(1)

    success = backup_rebuild_copy(dist_dir, aw_static_path)
    
    if not success:
        print("\n❌ failed. You can try manual operation:")
        print(f"sudo mv {aw_static_path} {aw_static_path}.backup")
        print(f"sudo cp -r {dist_dir} {aw_static_path}")
        print(f"sudo rm -rf {aw_static_path}.backup")
        sys.exit(1)

    print("\n=== Step 4: Restart ActivityWatch service ===")
    print(">>> Stopping all running activitywatch processes...")
    subprocess.call(["pkill", "-f", "activitywatch"], stderr=subprocess.DEVNULL)
    
    if platform.system() == "Darwin":
        aw_app = Path("/Applications/ActivityWatch.app")
        if aw_app.exists():
            print(">>> Starting ActivityWatch...")
            subprocess.Popen(
                ["open", "-a", "ActivityWatch"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
    elif platform.system() == "Linux":
        print(">>> Starting ActivityWatch server on Linux...")
        run("/home/trustme/activitywatch/aw-server/aw-server &")

    print("\naw-webui has been successfully deployed to ActivityWatch static directory.")
    print("🌐 Visit http://localhost:5600 to see the updated interface")
    print()

if __name__ == "__main__":
    main()







