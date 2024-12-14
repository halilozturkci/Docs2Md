from setuptools import setup, find_packages

setup(
    name="docs2md",
    version="0.1.0",
    packages=find_packages(include=['docs2md', 'docs2md.*']),
    install_requires=[
        "beautifulsoup4>=4.9.3",
        "selenium>=4.0.0",
        "playwright>=1.20.0",
        "httpx>=0.24.0",
        "html2text>=2020.1.16",
        "2captcha-python>=1.2.0",
        "click>=8.0.0",
        "rich>=10.0.0",
        "pyyaml>=5.4.0",
        "humanize>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "docs2md=docs2md.main:cli",
        ],
    },
    python_requires=">=3.8",
    author="ADEO AI",
    description="A tool for converting web documentation to Markdown format",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
) 