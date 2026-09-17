"""
Módulo para manejo de moléculas cargo (enzimas, fármacos, etc).
Encapsula la lógica de manejo de moléculas a empaquetar.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from pymol import cmd
    import numpy as np
    PYMOL_AVAILABLE = True
except ImportError:
    PYMOL_AVAILABLE = False
    print("Advertencia: PyMOL/NumPy no disponible. Algunas funciones estarán limitadas.")

from .config import ConfigManager


class Cargo:
    """
    Representa molécula cargo para empaquetamiento en cápside.

    Esta clase maneja enzimas u otras moléculas que serán empaquetadas,
    incluyendo su carga, centrado y validación.
    """

    def __init__(self, pdb_path: str, cargo_type: str = "enzyme",
                 config: Optional[ConfigManager] = None):
        """
        Inicializa cargo desde archivo PDB.

        Args:
            pdb_path: Ruta al archivo PDB del cargo
            cargo_type: Tipo de cargo ('enzyme', 'drug', 'nanoparticle', etc.)
            config: Gestor de configuración (opcional)

        Raises:
            FileNotFoundError: Si el archivo PDB no existe
        """
        self.pdb_path = str(Path(pdb_path).absolute())
        self.cargo_type = cargo_type
        self.config = config or ConfigManager()
        self.centered_path = None
        self.molecular_weight = None
        self.volume = None
        self.atom_count = None

        # Validar que el archivo existe
        if not os.path.exists(self.pdb_path):
            raise FileNotFoundError(f"Archivo PDB no encontrado: {self.pdb_path}")

        # Nombre base para operaciones PyMOL
        self.pymol_name = Path(pdb_path).stem

    def center_structure(self, output_path: Optional[str] = None) -> str:
        """
        Centra estructura en origen de coordenadas.

        Este método es crítico para el empaquetamiento ya que Packmol
        espera que las moléculas estén centradas en el origen.

        Args:
            output_path: Ruta archivo salida (opcional).
                        Si no se proporciona, usa enzima_centered.pdb

        Returns:
            Ruta al archivo centrado

        Raises:
            RuntimeError: Si PyMOL no está disponible
        """
        if not PYMOL_AVAILABLE:
            raise RuntimeError("PyMOL es requerido para centrar estructura")

        if output_path is None:
            # Usar ruta absoluta para el archivo centrado
            base_path = Path(self.pdb_path).resolve()
            output_path = str(base_path.parent / f"{base_path.stem}_centered.pdb")

        try:
            cmd.reinitialize()
            cmd.load(self.pdb_path, "cargo")

            # Obtener coordenadas y calcular centro
            coords = cmd.get_coords("cargo")
            if coords is not None and len(coords) > 0:
                # Centro de masa
                com = np.mean(coords, axis=0)

                # Trasladar al origen
                cmd.alter_state(1, "cargo", f"x = x - {com[0]}")
                cmd.alter_state(1, "cargo", f"y = y - {com[1]}")
                cmd.alter_state(1, "cargo", f"z = z - {com[2]}")

                print(f"Estructura centrada. Centro original: ({com[0]:.2f}, {com[1]:.2f}, {com[2]:.2f})")
            else:
                print("Advertencia: No se pudieron obtener coordenadas para centrar")

            # Guardar estructura centrada
            cmd.save(output_path, "cargo")
            cmd.delete("all")

            self.centered_path = output_path
            print(f"Cargo centrado guardado en: {output_path}")

            return output_path

        except Exception as e:
            raise RuntimeError(f"Error centrando cargo: {e}")

    def calculate_properties(self) -> Dict[str, Any]:
        """
        Calcula propiedades moleculares básicas.

        Returns:
            Diccionario con propiedades calculadas
        """
        properties = {
            'pdb_path': self.pdb_path,
            'cargo_type': self.cargo_type,
            'centered_path': self.centered_path
        }

        # Contar átomos y estimar propiedades
        try:
            atom_count = 0
            with open(self.pdb_path, 'r') as f:
                for line in f:
                    if line.startswith(('ATOM', 'HETATM')):
                        atom_count += 1

            self.atom_count = atom_count
            properties['atom_count'] = atom_count

            # Estimación muy aproximada del peso molecular
            # Promedio ~110 Da por residuo es una aproximación común
            properties['estimated_weight'] = atom_count * 12  # Da

            # Estimación del volumen (muy aproximada)
            # ~1.2 Å³ por Da es una aproximación para proteínas
            properties['estimated_volume'] = atom_count * 12 * 1.2  # Å³

        except Exception as e:
            print(f"Error calculando propiedades: {e}")

        return properties

    def validate_structure(self) -> bool:
        """
        Valida integridad de la estructura PDB.

        Returns:
            True si la estructura es válida para empaquetamiento
        """
        if not os.path.exists(self.pdb_path):
            return False

        # Verificar que el archivo no esté vacío
        if os.path.getsize(self.pdb_path) == 0:
            return False

        # Verificar que tenga líneas ATOM o HETATM
        has_atoms = False
        atom_count = 0

        try:
            with open(self.pdb_path, 'r') as f:
                for line in f:
                    if line.startswith(('ATOM', 'HETATM')):
                        has_atoms = True
                        atom_count += 1

            # Verificar que tiene un número razonable de átomos
            # Una enzima típica tiene al menos 1000 átomos
            if atom_count < 10:
                print(f"Advertencia: El cargo tiene muy pocos átomos ({atom_count})")
                return False

            return has_atoms

        except Exception as e:
            print(f"Error validando estructura: {e}")
            return False

    def prepare_for_packing(self) -> str:
        """
        Prepara el cargo para empaquetamiento.

        Esto incluye centrado y cualquier otra preparación necesaria.

        Returns:
            Ruta al archivo preparado
        """
        # Validar estructura primero
        if not self.validate_structure():
            raise ValueError(f"Estructura no válida para empaquetamiento: {self.pdb_path}")

        # Centrar estructura si no se ha hecho
        if self.centered_path is None:
            self.center_structure()

        return self.centered_path or self.pdb_path

    def get_packing_info(self) -> Dict[str, Any]:
        """
        Obtiene información relevante para empaquetamiento.

        Returns:
            Diccionario con información para el motor de empaquetamiento
        """
        # Calcular propiedades si no se ha hecho
        if self.atom_count is None:
            self.calculate_properties()

        return {
            'pdb_file': self.centered_path or self.pdb_path,
            'atom_count': self.atom_count,
            'cargo_type': self.cargo_type,
            # Radio de exclusión entre copias del cargo
            'exclusion_radius': self.config.get('packing.exclusion_radius', 5.0)
        }

    def __str__(self) -> str:
        """
        Representación string del cargo.
        """
        return f"Cargo(pdb='{Path(self.pdb_path).name}', type='{self.cargo_type}')"

    def __repr__(self) -> str:
        """
        Representación para debugging.
        """
        return self.__str__()