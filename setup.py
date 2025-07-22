from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="polarisllm",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="High-performance multi-model LLM runtime engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/polarisLLM",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": ["pytest", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "polaris=src.cli:main",
            "polarisllm=main:main",
            "polaris-server=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "config/models/*.yaml"],
    },
)