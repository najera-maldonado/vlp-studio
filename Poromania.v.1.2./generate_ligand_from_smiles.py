#!/usr/bin/env python3
"""
Generador automático de ligando desde SMILES para docking
"""

import argparse
import sys
import os
from pathlib import Path

def check_dependencies():
    """Verifica las dependencias necesarias"""
    missing = []

    try:
        import rdkit
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        missing.append("rdkit")

    # Verificar obabel
    if os.system("which obabel > /dev/null 2>&1") != 0:
        missing.append("obabel (OpenBabel)")

    if missing:
        print(f"❌ Dependencias faltantes: {', '.join(missing)}")
        print("\nPara instalar:")
        if "rdkit" in missing:
            print("  conda install -c conda-forge rdkit")
        if "obabel" in missing:
            print("  sudo apt-get install openbabel")
        return False

    return True

def smiles_to_3d_mol(smiles_code):
    """Convierte SMILES a molécula 3D con RDKit - versión mejorada para moléculas complejas"""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    try:
        # Crear molécula desde SMILES
        mol = Chem.MolFromSmiles(smiles_code)
        if mol is None:
            raise ValueError("SMILES inválido")

        # Agregar hidrógenos
        mol = Chem.AddHs(mol)

        print(f"Molécula: {Chem.rdMolDescriptors.CalcMolFormula(mol)}")
        print(f"Átomos: {mol.GetNumAtoms()}")
        print(f"Enlaces rotables: {Chem.rdMolDescriptors.CalcNumRotatableBonds(mol)}")

        # Estrategia múltiple para generar coordenadas 3D
        success = False

        # Método 1: Embed estándar con múltiples intentos
        for seed in [42, 123, 456, 789, 999]:
            try:
                if AllChem.EmbedMolecule(mol, randomSeed=seed) != -1:
                    print(f"✓ Embed exitoso con seed {seed}")
                    success = True
                    break
            except:
                continue

        # Método 2: Embed con parámetros relajados
        if not success:
            try:
                ps = AllChem.ETKDG()
                ps.randomSeed = 42
                ps.maxAttempts = 100
                ps.numThreads = 1
                if AllChem.EmbedMolecule(mol, ps) != -1:
                    print("✓ Embed exitoso con ETKDG")
                    success = True
            except:
                pass

        # Método 3: Embed básico sin semilla
        if not success:
            try:
                if AllChem.EmbedMolecule(mol) != -1:
                    print("✓ Embed exitoso sin semilla")
                    success = True
            except:
                pass

        if not success:
            raise ValueError("No se pudieron generar coordenadas 3D")

        # Optimización de geometría con manejo de errores
        try:
            result = AllChem.MMFFOptimizeMolecule(mol, maxIters=2000)
            if result == 0:
                print("✓ Optimización MMFF exitosa")
            else:
                print(f"⚠️ Optimización MMFF parcial (código: {result})")
        except:
            try:
                # Fallback: optimización UFF
                result = AllChem.UFFOptimizeMolecule(mol, maxIters=1000)
                if result == 0:
                    print("✓ Optimización UFF exitosa")
                else:
                    print(f"⚠️ Optimización UFF parcial (código: {result})")
            except:
                print("⚠️ Sin optimización - usando geometría inicial")

        return mol

    except Exception as e:
        raise ValueError(f"Error procesando SMILES: {e}")

def save_mol_as_sdf(mol, output_path):
    """Guarda molécula como archivo SDF"""
    from rdkit import Chem

    writer = Chem.SDWriter(str(output_path))
    writer.write(mol)
    writer.close()

def convert_sdf_to_pdbqt(sdf_path, pdbqt_path, ph=7.4):
    """Convierte SDF a PDBQT usando OpenBabel"""
    cmd = f"obabel '{sdf_path}' -O '{pdbqt_path}' -p {ph} --partialcharge gasteiger --errorlevel 1"

    result = os.system(cmd)
    if result != 0:
        raise RuntimeError("Error convirtiendo SDF a PDBQT")

    if not Path(pdbqt_path).exists() or Path(pdbqt_path).stat().st_size == 0:
        raise RuntimeError("Archivo PDBQT no generado correctamente")

def generate_ligand_info(smiles_code, mol, output_dir):
    """Genera archivo de información del ligando"""
    from rdkit import Chem
    from rdkit.Chem import Descriptors

    info_path = Path(output_dir) / "ligand_info.txt"

    # Calcular propiedades moleculares
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    rotatable = Descriptors.NumRotatableBonds(mol)
    tpsa = Descriptors.TPSA(mol)

    with open(info_path, 'w') as f:
        f.write("INFORMACIÓN DEL LIGANDO\n")
        f.write("=" * 50 + "\n")
        f.write(f"SMILES: {smiles_code}\n")
        f.write(f"Fórmula molecular: {Chem.rdMolDescriptors.CalcMolFormula(mol)}\n")
        f.write(f"Peso molecular: {mw:.2f} Da\n")
        f.write(f"LogP: {logp:.2f}\n")
        f.write(f"Donadores H: {hbd}\n")
        f.write(f"Aceptores H: {hba}\n")
        f.write(f"Enlaces rotables: {rotatable}\n")
        f.write(f"TPSA: {tpsa:.2f} Ų\n")
        f.write("\nRegla de Lipinski:\n")
        f.write(f"  MW ≤ 500: {'✓' if mw <= 500 else '✗'} ({mw:.1f})\n")
        f.write(f"  LogP ≤ 5: {'✓' if logp <= 5 else '✗'} ({logp:.1f})\n")
        f.write(f"  HBD ≤ 5: {'✓' if hbd <= 5 else '✗'} ({hbd})\n")
        f.write(f"  HBA ≤ 10: {'✓' if hba <= 10 else '✗'} ({hba})\n")

    print(f"📋 Información guardada: {info_path}")

def main():
    parser = argparse.ArgumentParser(description='Genera ligando PDBQT desde SMILES')
    parser.add_argument('smiles', help='Código SMILES del ligando')
    parser.add_argument('-o', '--output', default='ligand.pdbqt', help='Archivo PDBQT de salida')
    parser.add_argument('--ph', type=float, default=7.4, help='pH para protonación (default: 7.4)')
    parser.add_argument('--info', action='store_true', help='Generar archivo de información molecular')

    args = parser.parse_args()

    print("🧪 GENERADOR DE LIGANDO DESDE SMILES")
    print("=" * 50)

    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)

    print(f"📝 SMILES: {args.smiles}")
    print(f"📁 Salida: {args.output}")
    print(f"🧬 pH: {args.ph}")

    try:
        # Convertir SMILES a molécula 3D
        print("\n🔄 Generando estructura 3D...")
        mol = smiles_to_3d_mol(args.smiles)
        print("✓ Estructura 3D generada")

        # Crear directorio de salida si no existe
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar como SDF temporal
        temp_sdf = output_path.with_suffix('.sdf')
        save_mol_as_sdf(mol, temp_sdf)
        print(f"✓ SDF temporal: {temp_sdf}")

        # Convertir a PDBQT
        print("🔄 Convirtiendo a PDBQT...")
        convert_sdf_to_pdbqt(temp_sdf, output_path, args.ph)
        print(f"✓ PDBQT generado: {output_path}")

        # Generar información si se solicita
        if args.info:
            print("🔄 Generando información molecular...")
            generate_ligand_info(args.smiles, mol, output_path.parent)

        # Limpiar archivo temporal
        temp_sdf.unlink()
        print("✓ Archivos temporales eliminados")

        # Verificar resultado final
        if output_path.exists() and output_path.stat().st_size > 0:
            print(f"\n🎉 ¡Ligando generado exitosamente!")
            print(f"   Archivo: {output_path}")
            print(f"   Tamaño: {output_path.stat().st_size} bytes")
            print(f"\n💡 Para usar en docking: ./5docking.sh")
        else:
            raise RuntimeError("Error: archivo PDBQT vacío o no generado")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()