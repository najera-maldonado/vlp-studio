#!/usr/bin/env python3
"""
Script de prueba con ejemplos de SMILES comunes
"""

# Ejemplos de SMILES para probar
EJEMPLOS_SMILES = {
    "aspirina": "CC(=O)OC1=CC=CC=C1C(=O)O",
    "ibuprofeno": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
    "paracetamol": "CC(=O)NC1=CC=C(C=C1)O",
    "cafeina": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "glucosa": "C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O",
    "atp": "C1=NC(=C2C(=N1)N(C=N2)[C@H]3[C@@H]([C@@H]([C@H](O3)COP(=O)(O)OP(=O)(O)OP(=O)(O)O)O)O)N",
    "simple": "CCO",  # Etanol - muy simple para probar
    "benzeno": "C1=CC=CC=C1"
}

def main():
    print("🧪 EJEMPLOS DE SMILES PARA DOCKING")
    print("=" * 50)
    print("Usa cualquiera de estos códigos SMILES:")
    print()

    for nombre, smiles in EJEMPLOS_SMILES.items():
        print(f"📋 {nombre.upper()}")
        print(f"   SMILES: {smiles}")
        print(f"   Comando: python smiles_docking_pipeline.py '{smiles}' --ligand-name {nombre}")
        print()

    print("💡 Ejemplos de uso:")
    print()
    print("# Generar solo el ligando:")
    print("python generate_ligand_from_smiles.py 'CCO' -o etanol.pdbqt --info")
    print()
    print("# Pipeline completo (SMILES → Docking):")
    print("python smiles_docking_pipeline.py 'CC(=O)OC1=CC=CC=C1C(=O)O' --ligand-name aspirina")
    print()
    print("# Modo dry-run (solo mostrar comandos):")
    print("python smiles_docking_pipeline.py 'CCO' --ligand-name etanol --dry-run")
    print()
    print("📚 Dependencias necesarias:")
    print("   - RDKit: conda install -c conda-forge rdkit")
    print("   - OpenBabel: sudo apt-get install openbabel")
    print("   - iDock: para el docking molecular")

if __name__ == "__main__":
    main()