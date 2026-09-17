#!/usr/bin/env python3
"""
Script simple para ejecutar el analizador de poros
"""

import os
import sys

def main():
    """
    Ejecuta el analizador de poros con PyMOL
    """
    print("Iniciando PyMOL para análisis de poros...")
    print("Archivo: poronatural.pdb")
    print()

    # Ejecutar el script principal con PyMOL
    os.system("pymol -c pore_analyzer.py")

if __name__ == "__main__":
    main()