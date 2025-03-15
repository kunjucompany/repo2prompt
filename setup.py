from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="repo2prompt",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A wrapper around code2prompt to generate prompts from GitHub repositories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/repo2prompt",
    packages=find_packages(),
    py_modules=["repo2prompt"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[],  # No Python package dependencies - code2prompt CLI must be installed separately via cargo
    entry_points={
        "console_scripts": [
            "repo2prompt=repo2prompt:main",
        ],
    },
)