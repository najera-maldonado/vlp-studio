#!/usr/bin/env python
"""
Setup script for Nanocapsule Designer MVP
"""

import os
import sys
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f
                   if line.strip() and not line.startswith('#')]

# Filter out optional dependencies
core_requirements = [req for req in requirements
                    if not any(x in req.lower() for x in ['pytest', 'black', 'flake8'])]

dev_requirements = [
    'pytest>=7.4.0',
    'pytest-cov>=4.1.0',
    'black>=23.7.0',
    'flake8>=6.0.0',
]

setup(
    name='nanocapsule-designer',
    version='1.0.0',
    author='najera-maldonado',
    author_email='',
    description='Professional system for designing and packaging therapeutic enzymes in viral capsids',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/najera-maldonado/vlp-studio',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        '': ['*.yaml', '*.yml', '*.html', '*.js', '*.css'],
        'web': ['templates/*', 'static/*'],
    },
    python_requires='>=3.7',
    install_requires=core_requirements,
    extras_require={
        'dev': dev_requirements,
        'all': core_requirements + dev_requirements,
    },
    # (Sin console_scripts: no existe CLI. El punto de entrada es el servidor web
    #  `python src/web/app.py`. Se declaraba `cli.main:cli`, que no existe → se retiró.)
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Chemistry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    keywords='molecular-dynamics, protein-packing, capsid, enzyme, packmol, pymol',
    project_urls={
        'Bug Reports': 'https://github.com/najera-maldonado/vlp-studio/issues',
        'Source': 'https://github.com/najera-maldonado/vlp-studio',
        'Documentation': 'https://github.com/najera-maldonado/vlp-studio/wiki',
    },
)

# Post-installation message
def post_install_message():
    """Display post-installation instructions"""
    print("\n" + "="*60)
    print("Nanocapsule Designer MVP - Installation Complete!")
    print("="*60)
    print("\nIMPORTANT: Additional dependencies required:")
    print("1. Packmol: Install via your package manager")
    print("   - Ubuntu/Debian: sudo apt-get install packmol")
    print("   - macOS: brew install packmol")
    print("   - Or download from: http://m3g.iqm.unicamp.br/packmol/")
    print("\n2. PyMOL: Install via conda or package manager")
    print("   - conda install -c schrodinger pymol-open-source")
    print("   - Or: sudo apt-get install pymol")
    print("\nTo start the web server:")
    print("   python src/web/app.py")
    print("\nThen open: http://localhost:5000")
    print("="*60 + "\n")

if 'install' in sys.argv or 'develop' in sys.argv:
    post_install_message()