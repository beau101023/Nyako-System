import subprocess

from setuptools import setup
from setuptools.command.install import install

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        # Download unidic after melotts has been installed
        try:
            subprocess.check_call(["python", "-m", "unidic", "download"])
        except subprocess.CalledProcessError:
            print("Failed to download unidic")

setup(
    name="nyako-system",
    version="1.0",
    install_requires=requirements,
    packages=[],
    py_modules=["main"],
    entry_points={
        "console_scripts": [
            "nyako = main:main",
        ],
    },
    cmdclass={
        'install': PostInstallCommand,
    },
)
