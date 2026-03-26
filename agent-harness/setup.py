"""Setup for cli-anything-pytrends."""

from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-pytrends",
    version="0.1.0",
    description="CLI harness for Google Trends via pytrends",
    long_description=open("cli_anything/pytrends/README.md").read(),
    long_description_content_type="text/markdown",
    author="cli-anything",
    license="MIT",
    python_requires=">=3.8",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    include_package_data=True,
    package_data={
        "cli_anything.pytrends": ["skills/*.md", "README.md"],
    },
    install_requires=[
        "pytrends>=4.9",
        "click>=8.0",
        "pandas>=1.0",
        "requests>=2.0",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-pytrends=cli_anything.pytrends.pytrends_cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
