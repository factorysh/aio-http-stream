from setuptools import setup, find_packages

setup(
    name="aiohttp-stream",
    version="0.1",
    description="",
    url="https://github.com/factorysh/aiohttp-stream",
    install_requires=["aiohttp",],
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    extras_require={"test": ["pytest", "pytest-cov", "pytest-mock", "pytest-asyncio"],},
    license="3 terms BSD",
    classifiers=[
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
