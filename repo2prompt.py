#!/usr/bin/env python3
"""
repo2prompt - A wrapper around code2prompt to generate prompts from GitHub repositories.
This tool allows you to pull any GitHub repository, navigate to a specific subdirectory,
and generate an LLM prompt using code2prompt.
"""

import os
import sys
import argparse
import tempfile
import shutil
import subprocess
import site
import platform
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any, Union

def get_scripts_dir():
    """Get the appropriate scripts directory based on the platform and Python version."""
    if platform.system() == "Windows":
        # Get the user's site-packages scripts directory with Python version
        python_version = f"Python{sys.version_info.major}{sys.version_info.minor}"
        user_scripts_dir = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "Python" / python_version / "Scripts"
        
        # If that doesn't exist, try the site.USER_BASE approach
        if not user_scripts_dir.exists():
            user_scripts_dir = Path(site.USER_BASE) / "Scripts"
    else:
        # For Linux/MacOS
        user_scripts_dir = Path(site.USER_BASE) / "bin"
        
    return user_scripts_dir

def check_path_env():
    """Check if the script's directory is in the PATH environment variable."""
    if platform.system() == "Windows":
        # Get the user's site-packages scripts directory
        user_scripts_dir = get_scripts_dir()
        path_env = os.environ.get("PATH", "").split(os.pathsep)
        return str(user_scripts_dir) in path_env
    return True  # On non-Windows platforms, we don't need to modify PATH

def add_to_path_env():
    """Add the script's directory to the PATH environment variable."""
    if platform.system() != "Windows":
        return  # Only needed for Windows
        
    user_scripts_dir = get_scripts_dir()
    
    # Check if directory exists
    if not user_scripts_dir.exists():
        print(f"Warning: Scripts directory {user_scripts_dir} does not exist.", file=sys.stderr)
        return
        
    # Different methods to update PATH
    
    # 1. For current session
    path_env = os.environ.get("PATH", "")
    if str(user_scripts_dir) not in path_env:
        os.environ["PATH"] = f"{user_scripts_dir}{os.pathsep}{path_env}"
        print(f"Added {user_scripts_dir} to PATH for current session.")
    
    # 2. Suggest permanent addition for future sessions
    python_version = f"Python{sys.version_info.major}{sys.version_info.minor}"
    print(f"\nNOTE: For permanent PATH updates, add this directory to your PATH:")
    print(f"    {user_scripts_dir}")
    print("You can do this by:")
    print("    1. Search for 'Edit environment variables for your account' in Windows")
    print("    2. Edit the PATH variable")
    print("    3. Add the directory above as a new entry")
    print("    4. Restart your command prompt")
    print("\nOr add this to your PowerShell profile ($PROFILE):")
    print(f'    $ENV:PATH += ";{user_scripts_dir}"')
    print("\nOr for Command Prompt, use:")
    print(f'    setx PATH "%PATH%;{user_scripts_dir}"\n')

def check_code2prompt_installed():
    """Check if code2prompt is installed and available in PATH."""
    try:
        subprocess.run(["code2prompt", "--version"], check=True, capture_output=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

class Repo2Prompt:
    def __init__(self):
        self.temp_dir = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _validate_github_url(self, url: str) -> bool:
        """Validate if the provided URL is a GitHub repository URL."""
        parsed_url = urlparse(url)
        return parsed_url.netloc in ['github.com', 'www.github.com']
    
    def _extract_repo_info(self, url: str) -> Dict[str, str]:
        """Extract repository owner and name from GitHub URL."""
        # Handle URLs with or without .git extension
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
            
        parts = url.split('/')
        if len(parts) < 5:
            raise ValueError(f"Invalid GitHub URL format: {url}")
            
        owner = parts[-2]
        repo = parts[-1]
        
        return {
            "owner": owner,
            "repo": repo
        }
    
    def _clone_repository(self, url: str, branch: Optional[str] = None) -> str:
        """Clone the GitHub repository to a temporary directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="repo2prompt_")
        
        cmd = ["git", "clone"]
        if branch:
            cmd.extend(["--branch", branch])
            
        cmd.extend([url, self.temp_dir])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return self.temp_dir
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")
    
    def _get_subdirectory_path(self, base_dir: str, subdirectory: Optional[str] = None) -> str:
        """Get the full path to the specified subdirectory."""
        if not subdirectory:
            return base_dir
            
        full_path = os.path.join(base_dir, subdirectory)
        if not os.path.exists(full_path):
            raise ValueError(f"Subdirectory '{subdirectory}' does not exist in the repository")
            
        return full_path
    
    def _run_code2prompt(self, 
                         directory: str, 
                         template: Optional[str] = None,
                         include: Optional[List[str]] = None,
                         exclude: Optional[List[str]] = None,
                         count_tokens: bool = False,
                         encoding: Optional[str] = None,
                         output: Optional[str] = None,
                         output_format: Optional[str] = None,
                         diff: bool = False,
                         line_number: bool = False,
                         no_codeblock: bool = False,
                         hidden: bool = False,
                         no_ignore: bool = False,
                         git_diff_branch: Optional[str] = None,
                         git_log_branch: Optional[str] = None) -> Dict[str, Any]:
        """Run code2prompt on the specified directory with given options."""
        cmd = ["code2prompt", directory]
        
        # Add optional arguments
        if template:
            cmd.extend(["--template", template])
        
        if include:
            include_str = ",".join(include)
            cmd.extend(["--include", include_str])
            
        if exclude:
            exclude_str = ",".join(exclude)
            cmd.extend(["--exclude", exclude_str])
            
        if count_tokens:
            cmd.append("--tokens")
            
        if encoding:
            cmd.extend(["--encoding", encoding])
            
        if output:
            cmd.extend(["--output", output])
            
        if output_format:
            cmd.extend(["-O", output_format])
            
        if diff:
            cmd.append("--diff")
            
        if line_number:
            cmd.append("--line-number")
            
        if no_codeblock:
            cmd.append("--no-codeblock")
            
        if hidden:
            cmd.append("--hidden")
            
        if no_ignore:
            cmd.append("--no-ignore")
            
        if git_diff_branch:
            cmd.extend(["--git-diff-branch", git_diff_branch])
            
        if git_log_branch:
            cmd.extend(["--git-log-branch", git_log_branch])
        
        # Run code2prompt
        try:
            # For JSON output, we'll parse the result
            if output_format == "json":
                cmd.extend(["-O", "json"])
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                import json
                return json.loads(result.stdout)
            else:
                # For other formats, we'll just run the command
                subprocess.run(cmd, check=True)
                return {"status": "success"}
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run code2prompt: {e.stderr}")
    
    def generate_prompt(self, 
                        github_url: str, 
                        subdirectory: Optional[str] = None,
                        branch: Optional[str] = None,
                        template: Optional[str] = None,
                        include: Optional[List[str]] = None,
                        exclude: Optional[List[str]] = None,
                        count_tokens: bool = False,
                        encoding: Optional[str] = None,
                        output: Optional[str] = None,
                        output_format: Optional[str] = None,
                        diff: bool = False,
                        line_number: bool = False,
                        no_codeblock: bool = False,
                        hidden: bool = False,
                        no_ignore: bool = False,
                        git_diff_branch: Optional[str] = None,
                        git_log_branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a prompt from a GitHub repository.
        
        Args:
            github_url: URL of the GitHub repository
            subdirectory: Optional path to a subdirectory within the repository
            branch: Optional branch to clone
            template: Optional path to a custom Handlebars template file
            include: Optional list of glob patterns to include files
            exclude: Optional list of glob patterns to exclude files
            count_tokens: Whether to count tokens in the generated prompt
            encoding: Optional tokenizer encoding (cl100k, p50k, etc.)
            output: Optional path to save the generated prompt
            output_format: Optional output format (json)
            diff: Whether to include Git diff output in the generated prompt
            line_number: Whether to add line numbers to source code blocks
            no_codeblock: Whether to disable wrapping code inside markdown code blocks
            hidden: Whether to include hidden files and directories
            no_ignore: Whether to skip .gitignore rules
            git_diff_branch: Optional branch to compare for Git diff
            git_log_branch: Optional branch to get Git log from
            
        Returns:
            Dictionary with the result of the operation
        """
        if not self._validate_github_url(github_url):
            raise ValueError(f"Invalid GitHub repository URL: {github_url}")
        
        # Clone the repository
        repo_dir = self._clone_repository(github_url, branch)
        
        # Get the subdirectory path
        target_dir = self._get_subdirectory_path(repo_dir, subdirectory)
        
        # Run code2prompt on the target directory
        return self._run_code2prompt(
            directory=target_dir,
            template=template,
            include=include,
            exclude=exclude,
            count_tokens=count_tokens,
            encoding=encoding,
            output=output,
            output_format=output_format,
            diff=diff,
            line_number=line_number,
            no_codeblock=no_codeblock,
            hidden=hidden,
            no_ignore=no_ignore,
            git_diff_branch=git_diff_branch,
            git_log_branch=git_log_branch
        )


def main():
    # Check if the script's directory is in PATH
    if not check_path_env():
        add_to_path_env()
    
    # Check if code2prompt is installed
    if not check_code2prompt_installed():
        print("Error: code2prompt is not installed or not in PATH.", file=sys.stderr)
        print("Please install code2prompt using cargo:", file=sys.stderr)
        print("    cargo install code2prompt", file=sys.stderr)
        print("For more information, visit: https://github.com/sampottinger/code2prompt", file=sys.stderr)
        sys.exit(1)
        
    parser = argparse.ArgumentParser(
        description="Generate LLM prompts from GitHub repositories using code2prompt"
    )
    
    parser.add_argument("github_url", help="URL of the GitHub repository")
    parser.add_argument("-s", "--subdirectory", help="Path to a subdirectory within the repository")
    parser.add_argument("-b", "--branch", help="Repository branch to clone")
    parser.add_argument("-t", "--template", help="Path to a custom Handlebars template file")
    parser.add_argument("-i", "--include", help="Comma-separated list of glob patterns to include files")
    parser.add_argument("-e", "--exclude", help="Comma-separated list of glob patterns to exclude files")
    parser.add_argument("--tokens", action="store_true", help="Count tokens in the generated prompt")
    parser.add_argument("--encoding", choices=["cl100k", "p50k", "p50k_edit", "r50k_base", "o200k_base"], 
                       help="Tokenizer encoding")
    parser.add_argument("-o", "--output", help="Path to save the generated prompt")
    parser.add_argument("-O", "--output-format", choices=["json"], help="Output format")
    parser.add_argument("--diff", action="store_true", help="Include Git diff output in the generated prompt")
    parser.add_argument("--line-number", action="store_true", help="Add line numbers to source code blocks")
    parser.add_argument("--no-codeblock", action="store_true", 
                       help="Disable wrapping code inside markdown code blocks")
    parser.add_argument("--hidden", action="store_true", help="Include hidden files and directories")
    parser.add_argument("--no-ignore", action="store_true", help="Skip .gitignore rules")
    parser.add_argument("--git-diff-branch", help="Branch to compare for Git diff")
    parser.add_argument("--git-log-branch", help="Branch to get Git log from")
    
    args = parser.parse_args()
    
    # Process comma-separated lists
    include = args.include.split(',') if args.include else None
    exclude = args.exclude.split(',') if args.exclude else None
    
    try:
        with Repo2Prompt() as r2p:
            result = r2p.generate_prompt(
                github_url=args.github_url,
                subdirectory=args.subdirectory,
                branch=args.branch,
                template=args.template,
                include=include,
                exclude=exclude,
                count_tokens=args.tokens,
                encoding=args.encoding,
                output=args.output,
                output_format=args.output_format,
                diff=args.diff,
                line_number=args.line_number,
                no_codeblock=args.no_codeblock,
                hidden=args.hidden,
                no_ignore=args.no_ignore,
                git_diff_branch=args.git_diff_branch,
                git_log_branch=args.git_log_branch
            )
            
            if args.output_format == "json":
                import json
                print(json.dumps(result, indent=2))
                
    except (ValueError, RuntimeError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()