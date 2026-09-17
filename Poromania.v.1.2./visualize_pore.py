#!/usr/bin/env python3
"""
Script para visualización completa del análisis de poros
"""

import os
import sys

def main():
    print("=== OPCIONES DE VISUALIZACIÓN ===")
    print("1. PyMOL con GUI completa (Recomendado)")
    print("2. Solo terminal (sin ventana gráfica)")

    while True:
        choice = input("\nSeleccione opción (1-2): ").strip()
        if choice in ['1', '2']:
            break
        print("Seleccione 1 o 2")

    if choice == '1':
        print("\nAbriendo PyMOL con interfaz gráfica...")
        print("INSTRUCCIONES:")
        print("- La ventana de PyMOL se abrirá automáticamente")
        print("- Use el mouse para rotar (izquierdo), zoom (scroll), mover (derecho)")
        print("- El terminal mostrará las opciones interactivas")
        print("- Puede cambiar colores, representaciones, etc. en PyMOL")
        print("\nPresione Enter para continuar...")
        input()
        os.system("python pore_analyzer.py --gui")

    elif choice == '2':
        print("\nEjecutando en modo terminal...")
        print("- Solo verá texto en el terminal")
        print("- Útil para generar mutantes sin visualización")
        os.system("python pore_analyzer.py")


if __name__ == "__main__":
    main()