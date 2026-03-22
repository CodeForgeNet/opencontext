from setuptools import setup, find_packages

setup(
    name="pcsl-sdk",
    version="1.0.0",
    packages=find_packages(),
    install_requires=["requests>=2.28"],
    author="Karan Singh",
    description="Python SDK for the PCSL (Personal Context Sovereignty Layer) protocol",
    url="https://github.com/karan/pcsl",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)
