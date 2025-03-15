# repo2prompt

A wrapper around [code2prompt](https://github.com/mufeedvh/code2prompt) that allows you to generate LLM prompts from any GitHub repository.

The primary use of this is to parse examples and docs of packages to a text file for passing to LLMs with large context. 

## Example usage

For generating prompt for example usages of pydantic-ai usages. 
 
```bash
repo2prompt https://github.com/pydantic/pydantic-ai -s docs/examples -o pydantic-examples.txt
```

## Features

- Pull any GitHub repository directly from its URL
- Focus on specific subdirectories within the repository
- Support for all code2prompt features:
  - Customizable prompt generation with Handlebars templates
  - File filtering using glob patterns
  - Token counting with various encodings
  - Git diff and log inclusion
  - Line numbers and formatting options
  - And more!

## Installation

### Requirements

- Python 3.6 or higher
- git
- cargo (Rust's package manager)
- code2prompt CLI tool

### Installation

1. Install code2prompt CLI tool using cargo:
```bash
cargo install code2prompt
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/repo2prompt.git
cd repo2prompt
```

3. Install the package:
```bash
pip install -e .
```

4. Add the Python scripts directory to your PATH:

For Windows PowerShell, add this to your profile (usually at `$PROFILE`):
```powershell
$ENV:PATH += ";$HOME\AppData\Roaming\Python\Python3xx\Scripts"  # Replace 3xx with your Python version
```

For Windows Command Prompt, use:
```cmd
setx PATH "%PATH%;%APPDATA%\Python\Python3xx\Scripts"  # Replace 3xx with your Python version
```

For Linux/MacOS, add to your ~/.bashrc or ~/.zshrc:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

After updating PATH, restart your terminal for changes to take effect.

## Usage

### Basic Usage

Generate a prompt from a GitHub repository:

```bash
repo2prompt https://github.com/username/repository
```

Generate a prompt from a specific subdirectory:

```bash
repo2prompt https://github.com/username/repository --subdirectory path/to/dir
```

### Advanced Options

Clone a specific branch:

```bash
repo2prompt https://github.com/username/repository --branch development
```

Use a custom template:

```bash
repo2prompt https://github.com/username/repository --template path/to/template.hbs
```

Include only specific file types:

```bash
repo2prompt https://github.com/username/repository --include "*.py,*.js"
```

Exclude certain file types