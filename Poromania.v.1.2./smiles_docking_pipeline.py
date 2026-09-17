#!/usr/bin/env python3
"""
Pipeline completo: SMILES → Ligando PDBQT → Docking automático
"""

import argparse
import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, description=""):
    """Ejecuta comando y maneja errores"""
    print(f"🔄 {description}")
    print(f"   Comando: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error en: {description}")
        print(f"   stderr: {result.stderr}")
        return False
    else:
        print(f"✓ Completado: {description}")
        if result.stdout.strip():
            print(f"   stdout: {result.stdout.strip()}")
        return True

def check_mutants():
    """Verifica que existan mutantes para docking"""
    mutants_dir = Path("mutants")
    if not mutants_dir.exists():
        return []

    mutants = list(mutants_dir.glob("mut_*"))
    return [m for m in mutants if m.is_dir() and (m / "receptor.pdb").exists()]

def main():
    parser = argparse.ArgumentParser(description='Pipeline completo SMILES → Docking')
    parser.add_argument('smiles', help='Código SMILES del ligando')
    parser.add_argument('--ligand-name', default='ligand', help='Nombre base del ligando')
    parser.add_argument('--ph', type=float, default=7.4, help='pH para protonación')
    parser.add_argument('--no-info', action='store_true', help='No generar archivo de información')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar comandos, no ejecutar')

    args = parser.parse_args()

    print("🚀 PIPELINE SMILES → DOCKING")
    print("=" * 60)
    print(f"📝 SMILES: {args.smiles}")
    print(f"🏷️  Ligando: {args.ligand_name}")
    print(f"🧬 pH: {args.ph}")

    if args.dry_run:
        print("🔍 MODO DRY-RUN - Solo mostrando comandos")

    # Verificar mutantes
    mutants = check_mutants()
    if not mutants:
        print("❌ No se encontraron mutantes en mutants/")
        print("   Ejecuta primero el análisis de poros y generación de mutantes")
        sys.exit(1)

    print(f"📁 Mutantes encontrados: {len(mutants)}")
    for m in mutants[:3]:  # Mostrar solo los primeros 3
        print(f"   - {m.name}")
    if len(mutants) > 3:
        print(f"   ... y {len(mutants) - 3} más")

    # Paso 1: Generar ligando desde SMILES
    ligand_file = f"{args.ligand_name}.pdbqt"
    info_flag = "" if args.no_info else "--info"

    cmd1 = f"python generate_ligand_from_smiles.py '{args.smiles}' -o {ligand_file} --ph {args.ph} {info_flag}"

    if args.dry_run:
        print(f"\n1️⃣ Generación de ligando:")
        print(f"   {cmd1}")
    else:
        print(f"\n1️⃣ Generando ligando desde SMILES...")
        if not run_command(cmd1, f"Generar {ligand_file}"):
            sys.exit(1)

        # Verificar que el ligando se generó correctamente
        if not Path(ligand_file).exists():
            print(f"❌ Error: No se generó {ligand_file}")
            sys.exit(1)

        ligand_size = Path(ligand_file).stat().st_size
        print(f"✓ Ligando generado: {ligand_file} ({ligand_size} bytes)")

    # Paso 2: Preparar para docking (renombrar a ligand.pdbqt si es necesario)
    if args.ligand_name != "ligand":
        cmd2 = f"cp {ligand_file} ligand.pdbqt"

        if args.dry_run:
            print(f"\n2️⃣ Preparación para docking:")
            print(f"   {cmd2}")
        else:
            print(f"\n2️⃣ Preparando para docking...")
            if not run_command(cmd2, "Copiar ligando como ligand.pdbqt"):
                sys.exit(1)

    # Paso 3: Ejecutar docking
    cmd3 = "./5docking.sh"

    if args.dry_run:
        print(f"\n3️⃣ Docking molecular:")
        print(f"   {cmd3}")
        print(f"\n📊 Resultados esperados:")
        for m in mutants:
            print(f"   - {m.name}/docking/Results/")
            print(f"   - {m.name}/docking/estructuras/")
    else:
        print(f"\n3️⃣ Ejecutando docking molecular...")
        if not run_command(cmd3, "Docking en todos los mutantes"):
            print("⚠️  Advertencia: Algunos dockings pueden haber fallado")
            print("   Revisa los logs individuales en mutants/*/mut_*.log")

        # Verificar resultados
        print(f"\n📊 Verificando resultados...")
        successful = 0
        failed = 0

        for mutant in mutants:
            result_file = mutant / "docking" / "Results" / "ligand.pdbqt"
            if result_file.exists() and result_file.stat().st_size > 0:
                successful += 1
                # Obtener mejor score si existe
                poses_file = mutant / "docking" / "Results" / "poses.txt"
                if poses_file.exists():
                    try:
                        with open(poses_file) as f:
                            first_line = f.readline().strip()
                            if first_line:
                                pose, score = first_line.split('\t')
                                print(f"   ✓ {mutant.name}: Mejor score = {score} kcal/mol")
                            else:
                                print(f"   ✓ {mutant.name}: Docking completado")
                    except:
                        print(f"   ✓ {mutant.name}: Docking completado")
                else:
                    print(f"   ✓ {mutant.name}: Docking completado")
            else:
                failed += 1
                print(f"   ❌ {mutant.name}: Sin resultados")

        print(f"\n🎯 Resumen:")
        print(f"   ✓ Exitosos: {successful}/{len(mutants)}")
        print(f"   ❌ Fallidos: {failed}/{len(mutants)}")

        if successful > 0:
            print(f"\n📁 Resultados en:")
            print(f"   mutants/*/docking/Results/")
            print(f"   mutants/*/docking/estructuras/")

    if not args.dry_run:
        print(f"\n🎉 Pipeline completado!")
        print(f"💡 Para ver poses: pymol mutants/mut_*/docking/estructuras/*.pdb")

if __name__ == "__main__":
    main()