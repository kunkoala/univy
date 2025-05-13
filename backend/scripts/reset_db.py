import os
import subprocess
import sys
import argparse
from pathlib import Path

def run_command(command: str, cwd: str = None) -> bool:
    """Run a shell command and return True if successful."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Command executed successfully: {command}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error output: {e.stderr}")
        return False

def reset_database(migrations_path: str = None):
    """
    Reset the database by running Alembic commands.
    
    Args:
        migrations_path (str, optional): Path to the migrations folder. 
            If not provided, defaults to 'migrations' in the project root.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Change to the project root directory
    os.chdir(project_root)
    
    # Set migrations path
    if migrations_path:
        alembic_dir = Path(migrations_path)
        if not alembic_dir.exists():
            print(f"Error: Migrations directory not found: {alembic_dir}")
            sys.exit(1)
    else:
        alembic_dir = project_root / "alembic"
        if not alembic_dir.exists():
            print(f"Error: Default alembic directory not found: {alembic_dir}")
            sys.exit(1)
    
    # Step 1: Downgrade to base
    print("\nStep 1: Downgrading database to base...")
    if not run_command("alembic downgrade base"):
        print("Failed to downgrade database")
        sys.exit(1)
    
    # Step 2: Remove existing migrations
    print("\nStep 2: Removing existing migrations...")
    versions_dir = alembic_dir / "versions"
    if versions_dir.exists():
        for file in versions_dir.glob("*.py"):
            try:
                file.unlink()
                print(f"Removed: {file}")
            except Exception as e:
                print(f"Error removing {file}: {e}")
    
    # Step 3: Create new initial migration
    print("\nStep 3: Creating new initial migration...")
    if not run_command('alembic revision --autogenerate -m "init table"'):
        print("Failed to create new migration")
        sys.exit(1)
    
    # Step 4: Upgrade to head
    print("\nStep 4: Upgrading database to head...")
    if not run_command("alembic upgrade head"):
        print("Failed to upgrade database")
        sys.exit(1)
    
    print("\nDatabase reset completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset the database using Alembic commands")
    parser.add_argument(
        "--migrations",
        "-m",
        type=str,
        help="Path to the migrations folder (default: migrations in project root)",
        default=None
    )
    
    args = parser.parse_args()
    reset_database(args.migrations) 