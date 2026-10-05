"""
Módulo para manejo de estructuras de cápsides virales.
Extrae y mejora funcionalidad de 1calcula_radio_interno.py
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from pymol import cmd, stored

    PYMOL_AVAILABLE = True
except ImportError:
    PYMOL_AVAILABLE = False
    print("Advertencia: PyMOL no está disponible. Algunas funciones estarán limitadas.")

from .config import ConfigManager
from .pdb_geometry import center_pdb


class Capsid:
    """
    Representa una cápside viral con métodos para análisis geométrico.

    Esta clase encapsula toda la lógica relacionada con cápsides,
    incluyendo carga de estructura, centrado y cálculo de radio interno.
    """

    def __init__(self, pdb_path: str, config: Optional[ConfigManager] = None):
        """
        Inicializa cápside desde archivo PDB.

        Args:
            pdb_path: Ruta al archivo PDB de la cápside
            config: Gestor de configuración (opcional)

        Raises:
            FileNotFoundError: Si el archivo PDB no existe
        """
        self.pdb_path = str(Path(pdb_path).absolute())
        self.config = config or ConfigManager()
        self.centered_path = None
        self.internal_radius = None
        # Procedencia del radio: "calculated" (PyMOL) o "default" (valor de reserva de la
        # config). Quien consuma el radio para un experimento debe comprobarlo: el valor
        # de reserva no distingue BMV (90 Å real) de una cápside cualquiera.
        self.radius_source: Optional[str] = None
        self.center = (0.0, 0.0, 0.0)

        # Validar que el archivo existe
        if not os.path.exists(self.pdb_path):
            raise FileNotFoundError(f"Archivo PDB no encontrado: {self.pdb_path}")

        # Nombre base para operaciones PyMOL
        self.pymol_name = Path(pdb_path).stem

    def calculate_internal_radius(self, save_to_file: bool = True) -> float:
        """
        Calcula el radio interno de la cápside usando colisión de pseudoátomo.

        Migrado desde 1calcula_radio_interno.py con el cambio importante:
        - Original: radio_colision + 1 Å
        - Nuevo: radio_colision - 1 Å (margen interno de seguridad)

        IMPORTANTE: La estructura se recentra en el origen antes del cálculo.

        Args:
            save_to_file: Si True, guarda el radio en radio_interno.txt

        Returns:
            Radio interno en Angstroms

        Raises:
            RuntimeError: Si PyMOL no está disponible o hay error en cálculo
        """
        if not PYMOL_AVAILABLE:
            # Si PyMOL no está disponible, usar valor por defecto
            default_radius = self.config.get("packing.internal_radius_default", 90.0)
            print(f"PyMOL no disponible. Usando radio por defecto: {default_radius} Å")
            self.internal_radius = default_radius
            self.radius_source = "default"
            return default_radius

        try:
            # Limpiar sesión PyMOL
            cmd.reinitialize()

            # Cargar cápside
            cmd.load(self.pdb_path, "capside")

            # Calcular centro geométrico ANTES de recentrar
            stored.xyz = [0.0, 0.0, 0.0]
            cmd.iterate_state(
                1, "capside", "stored.xyz[0] += x; stored.xyz[1] += y; stored.xyz[2] += z"
            )
            n_atoms = cmd.count_atoms("capside")

            if n_atoms == 0:
                raise RuntimeError("La cápside no contiene átomos")

            center_original = [coord / n_atoms for coord in stored.xyz]
            print(
                f"Centro original: ({center_original[0]:.2f}, {center_original[1]:.2f}, {center_original[2]:.2f})"
            )

            # IMPORTANTE: Recentrar en el origen antes de calcular radio
            cmd.alter_state(1, "capside", f"x = x - {center_original[0]}")
            cmd.alter_state(1, "capside", f"y = y - {center_original[1]}")
            cmd.alter_state(1, "capside", f"z = z - {center_original[2]}")
            print("Estructura recentrada en origen (0,0,0)")

            # El centro ahora es el origen
            self.center = (0.0, 0.0, 0.0)

            # Crear pseudoátomo en el origen (0,0,0)
            cmd.pseudoatom("centro", pos=[0.0, 0.0, 0.0], vdw=1.0)
            cmd.show("spheres", "centro")
            cmd.set("sphere_scale", 1.0, "centro")
            cmd.color("red", "centro")

            # Crear selección de cápside sin el centro
            cmd.select("capa", "capside and not centro")

            # Buscar colisión expandiendo radio del pseudoátomo
            print("\n=== Calculando radio interno de cápside ===")
            radio_colision = None
            colision_detectada = False

            # Rango de búsqueda: de 5 a 200 Angstroms
            for r in range(5, 200):
                cmd.alter("centro", f"vdw={r}")
                cmd.rebuild()

                # Buscar átomos cercanos
                cmd.select("cercano", f"byres (capa within {r + 0.5} of centro)")
                colisiones = cmd.count_atoms("cercano")

                if colisiones > 0 and not colision_detectada:
                    print(f"Primera colisión detectada a {r} Å ({colisiones} átomos)")
                    radio_colision = r
                    colision_detectada = True
                    break

            if radio_colision is None:
                # No se encontró colisión, usar valor por defecto
                radio_colision = self.config.get("packing.internal_radius_default", 90.0)
                print(f"No se detectó colisión. Usando radio por defecto: {radio_colision} Å")
                self.radius_source = "default"
            else:
                # DECISIÓN CIENTÍFICA PENDIENTE (CIENCIA-1, AUDITORIA_PACKING P-08/PK-06):
                # el código suma 1 Å como el script original; el docstring y la
                # documentación dicen restar. No se cambia aquí: es criterio del autor.
                radio_colision = radio_colision + 1.0
                print(f"Radio interno calculado: {radio_colision} Å (colisión + 1 Å)")
                self.radius_source = "calculated"

            self.internal_radius = radio_colision

            # Guardar en archivo si se solicita
            if save_to_file:
                output_file = "radio_interno.txt"
                with open(output_file, "w") as f:
                    f.write(f"{radio_colision}\n")
                print(f"Radio guardado en {output_file}")

            # Limpiar PyMOL
            cmd.delete("all")

            return radio_colision

        except Exception as e:
            print(f"Error calculando radio interno: {e}")
            # Usar valor por defecto en caso de error
            default_radius = self.config.get("packing.internal_radius_default", 90.0)
            self.internal_radius = default_radius
            self.radius_source = "default"
            return default_radius

    def center_structure(self, output_path: Optional[str] = None) -> str:
        """
        Centra la estructura en el origen de coordenadas (traslación por el centroide).

        No usa PyMOL: es una traslación de coordenadas en Python puro que conserva el
        resto del archivo (registros ``TER``, cabeceras). Es el mismo centroide
        (media aritmética de coordenadas) que usa ``calculate_internal_radius``.

        Args:
            output_path: Ruta archivo salida (opcional).
                        Si no se proporciona, usa <stem>_centered.pdb junto al original.

        Returns:
            Ruta al archivo centrado

        Raises:
            RuntimeError: Si la estructura no se puede centrar (sin átomos, E/S)
        """
        if output_path is None:
            # Usar ruta absoluta para el archivo centrado
            base_path = Path(self.pdb_path).resolve()
            output_path = str(base_path.parent / f"{base_path.stem}_centered.pdb")

        try:
            written, centroid = center_pdb(self.pdb_path, output_path)
        except (OSError, ValueError) as e:
            raise RuntimeError(f"Error centrando estructura: {e}") from e

        self.centered_path = written
        print(
            f"Estructura centrada guardada en: {written} "
            f"(centroide original: {centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f})"
        )
        return written

    def get_geometric_properties(self) -> Dict[str, Any]:
        """
        Obtiene propiedades geométricas de la cápside.

        Returns:
            Diccionario con propiedades calculadas
        """
        # Calcular radio si no se ha hecho
        if self.internal_radius is None:
            self.calculate_internal_radius(save_to_file=False)

        return {
            "internal_radius": self.internal_radius,
            "center": self.center,
            "pdb_path": self.pdb_path,
            "centered_path": self.centered_path,
            # Radio efectivo para empaquetamiento (con margen de colisión)
            "packing_radius": self.internal_radius
            - self.config.get("packing.collision_margin", 2.0),
        }

    def validate_structure(self) -> bool:
        """
        Valida que la estructura PDB sea apropiada para empaquetamiento.

        Returns:
            True si la estructura es válida, False en caso contrario
        """
        if not os.path.exists(self.pdb_path):
            return False

        # Verificar que el archivo no esté vacío
        if os.path.getsize(self.pdb_path) == 0:
            return False

        # Verificar que tenga líneas ATOM o HETATM
        has_atoms = False
        with open(self.pdb_path, "r") as f:
            for line in f:
                if line.startswith(("ATOM", "HETATM")):
                    has_atoms = True
                    break

        return has_atoms

    def __str__(self) -> str:
        """
        Representación string de la cápside.
        """
        return f"Capsid(pdb='{Path(self.pdb_path).name}', radius={self.internal_radius})"

    def __repr__(self) -> str:
        """
        Representación para debugging.
        """
        return self.__str__()
