"""
Módulo para obtener y preparar estructuras desde PDB.
Maneja la descarga de unidades biológicas completas para cápsides.
"""

from pathlib import Path
from typing import Optional

try:
    from pymol import cmd

    PYMOL_AVAILABLE = True
except ImportError:
    PYMOL_AVAILABLE = False
    print("Advertencia: PyMOL no disponible para fetch de estructuras")


class StructureFetcher:
    """
    Gestiona la obtención y preparación de estructuras desde PDB.

    Especialmente importante para cápsides virales que necesitan
    la unidad biológica completa, no solo la unidad asimétrica.
    """

    def __init__(self, output_dir: str = "."):
        """
        Inicializa el fetcher.

        Args:
            output_dir: Directorio donde guardar las estructuras
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def fetch_capsid(self, pdb_id: str, output_name: Optional[str] = None) -> str:
        """
        Descarga una cápside completa (unidad biológica).

        Para cápsides virales es crítico obtener la unidad biológica
        completa, no solo la unidad asimétrica del cristal.

        Args:
            pdb_id: Código PDB (ej: '1QBE', '2MS2')
            output_name: Nombre del archivo de salida (opcional)

        Returns:
            Ruta al archivo descargado

        Example:
            >>> fetcher = StructureFetcher()
            >>> fetcher.fetch_capsid('1QBE', 'QB_capsid.pdb')
        """
        if not PYMOL_AVAILABLE:
            raise RuntimeError("PyMOL es requerido para descargar estructuras")

        pdb_id = pdb_id.upper().strip()

        if output_name is None:
            output_name = f"capsid_{pdb_id}.pdb"

        output_path = self.output_dir / output_name

        try:
            print(f"Descargando cápside {pdb_id} (unidad biológica)...")

            # Limpiar sesión
            cmd.reinitialize()

            # PASO 1: Fetch con type=pdb1 para obtener unidad biológica
            # Esto es CRUCIAL para cápsides - DEBE ejecutarse PRIMERO
            print(f"   Ejecutando: fetch {pdb_id}, type=pdb1")
            cmd.fetch(pdb_id, type="pdb1")

            # PASO 2: Activar todos los estados DESPUÉS del fetch
            # Esto es CRÍTICO - debe ir en secuencia separada
            print("   Ejecutando: set all_states, on")
            cmd.set("all_states", "on")

            # Dar tiempo para que se procese
            cmd.refresh()

            # Asegurar que tenemos la estructura completa
            n_atoms = cmd.count_atoms(pdb_id)
            print(f"Estructura descargada: {n_atoms} átomos")

            if n_atoms < 1000:
                print(
                    f"Advertencia: Muy pocos átomos ({n_atoms}). "
                    "Puede que no sea la unidad biológica completa."
                )

            # Guardar estructura
            cmd.save(str(output_path), pdb_id)

            # Limpiar
            cmd.delete("all")

            print(f"Cápside guardada en: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error descargando {pdb_id}: {e}")

            # Intentar método alternativo
            return self._fetch_alternative(pdb_id, output_path)

    def fetch_enzyme(
        self, pdb_id: str, output_name: Optional[str] = None, chains: Optional[list] = None
    ) -> str:
        """
        Descarga una enzima o proteína desde PDB.

        Para enzimas generalmente queremos solo la proteína,
        sin agua ni ligandos pequeños.

        Args:
            pdb_id: Código PDB
            output_name: Nombre del archivo de salida
            chains: Lista de cadenas a mantener (opcional)

        Returns:
            Ruta al archivo descargado
        """
        if not PYMOL_AVAILABLE:
            raise RuntimeError("PyMOL es requerido para descargar estructuras")

        pdb_id = pdb_id.upper().strip()

        if output_name is None:
            output_name = f"enzyme_{pdb_id}.pdb"

        output_path = self.output_dir / output_name

        try:
            print(f"Descargando enzima {pdb_id}...")

            # Limpiar sesión
            cmd.reinitialize()

            # Fetch estándar para enzimas
            cmd.fetch(pdb_id)

            # Remover agua y ligandos pequeños
            cmd.remove("solvent")
            cmd.remove("organic")  # Remueve moléculas orgánicas pequeñas

            # Si se especificaron cadenas, mantener solo esas
            if chains:
                chains_str = "+".join(chains)
                cmd.select("enzyme", f"chain {chains_str}")
                cmd.save(str(output_path), "enzyme")
            else:
                cmd.save(str(output_path), pdb_id)

            n_atoms = cmd.count_atoms(pdb_id)
            print(f"Enzima descargada: {n_atoms} átomos")

            # Limpiar
            cmd.delete("all")

            print(f"Enzima guardada en: {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"Error descargando {pdb_id}: {e}")
            raise

    def _fetch_alternative(self, pdb_id: str, output_path: Path) -> str:
        """
        Método alternativo de descarga usando comandos específicos.

        Útil cuando el fetch estándar no obtiene la unidad biológica.
        """
        try:
            print(f"Intentando método alternativo para {pdb_id}...")

            cmd.reinitialize()

            # Comandos específicos para algunos casos conocidos
            if pdb_id == "1QBE":  # QB bacteriophage
                cmd.fetch("1QBE", type="pdb1")
                cmd.set("all_states", "on")

            elif pdb_id == "2MS2":  # MS2 bacteriophage
                cmd.fetch("2MS2", type="pdb1")
                cmd.set("all_states", "on")

            elif pdb_id == "1CWP":  # CCMV
                cmd.fetch("1CWP", type="pdb1")
                cmd.set("all_states", "on")

            else:
                # Genérico: intentar con pdb1
                cmd.fetch(pdb_id, type="pdb1")
                cmd.set("all_states", "on")

            # Guardar
            cmd.save(str(output_path), pdb_id)
            n_atoms = cmd.count_atoms(pdb_id)

            cmd.delete("all")

            print(f"Estructura alternativa guardada: {n_atoms} átomos")
            return str(output_path)

        except Exception as e:
            print(f"Método alternativo también falló: {e}")
            raise

    def list_available_capsides(self) -> list:
        """
        Lista todas las cápsides disponibles en Input/Capsides/.

        Returns:
            Lista de nombres de carpetas de cápsides disponibles
        """
        capsides_dir = self.output_dir / "Capsides"
        if not capsides_dir.exists():
            return []

        capsides = []
        for folder in capsides_dir.iterdir():
            if folder.is_dir():
                capsid_file = folder / "capside.pdb"
                if capsid_file.exists():
                    capsides.append(folder.name)

        return sorted(capsides)

    def list_available_enzymes(self) -> list:
        """
        Lista todas las enzimas disponibles en Input/Enzimas/.

        Returns:
            Lista de nombres de carpetas de enzimas disponibles
        """
        enzymes_dir = self.output_dir / "Enzimas"
        if not enzymes_dir.exists():
            return []

        enzymes = []
        for folder in enzymes_dir.iterdir():
            if folder.is_dir():
                enzyme_file = folder / "enzima.pdb"
                if enzyme_file.exists():
                    enzymes.append(folder.name)

        return sorted(enzymes)

    def get_structure_path(self, structure_type: str, structure_name: str) -> str:
        """
        Obtiene la ruta completa a un archivo de estructura.

        Args:
            structure_type: "capside" o "enzima"
            structure_name: Nombre de la carpeta de la estructura

        Returns:
            Ruta completa al archivo PDB
        """
        if structure_type == "capside":
            return str(self.output_dir / "Capsides" / structure_name / "capside.pdb")
        elif structure_type == "enzima":
            return str(self.output_dir / "Enzimas" / structure_name / "enzima.pdb")
        else:
            raise ValueError("structure_type debe ser 'capside' o 'enzima'")

    @staticmethod
    def prepare_examples():
        """
        Descarga y prepara las estructuras de ejemplo del proyecto.

        - QB (1QBE): Bacteriófago QB
        - GCase (1OGS): Glucocerebrosidasa
        """
        fetcher = StructureFetcher("../Input")

        print("\n=== Preparando Estructuras de Ejemplo ===\n")

        # Descargar cápside QB completa
        try:
            capsid_file = fetcher.fetch_capsid("1QBE", "QB_capsid_complete.pdb")
            print(f"Cápside QB lista: {capsid_file}")
        except Exception as e:
            print(f"Error con cápside: {e}")

        # Descargar enzima GCase
        try:
            enzyme_file = fetcher.fetch_enzyme("1OGS", "GCase_enzyme.pdb")
            print(f"Enzima GCase lista: {enzyme_file}")
        except Exception as e:
            print(f"Error con enzima: {e}")

        print("\n=== Estructuras de Ejemplo Preparadas ===")


if __name__ == "__main__":
    # Si se ejecuta directamente, preparar ejemplos
    StructureFetcher.prepare_examples()
