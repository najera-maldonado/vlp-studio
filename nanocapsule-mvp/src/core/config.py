"""
Gestor de configuración centralizada para Nanocapsule Designer.
Maneja la carga y acceso a parámetros de configuración desde archivos YAML.
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigManager:
    """
    Gestor centralizado de configuración del sistema.

    Carga configuración desde archivo YAML y proporciona acceso
    mediante notación de punto a los parámetros.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración.

        Args:
            config_path: Ruta al archivo de configuración YAML.
                        Si es None, busca config/default.yaml relativo al proyecto.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()

    def _get_default_config_path(self) -> str:
        """
        Obtiene la ruta por defecto del archivo de configuración.

        Returns:
            Ruta absoluta al archivo config/default.yaml
        """
        # Encontrar la raíz del proyecto (donde está nanocapsule-mvp)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent  # src/core -> src -> proyecto

        config_path = project_root / "config" / "default.yaml"

        if not config_path.exists():
            # Fallback: buscar relativo al directorio actual
            config_path = Path("config/default.yaml")

        return str(config_path)

    def _load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo YAML.

        Returns:
            Diccionario con la configuración cargada

        Raises:
            FileNotFoundError: Si el archivo de configuración no existe
            yaml.YAMLError: Si hay error parseando el YAML
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config or {}
        except FileNotFoundError:
            print(f"Advertencia: Archivo de configuración no encontrado: {self.config_path}")
            print("Usando configuración por defecto...")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parseando archivo de configuración: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retorna configuración por defecto hardcodeada.
        Usado como fallback cuando no hay archivo de configuración.

        Returns:
            Diccionario con configuración mínima por defecto
        """
        return {
            'packing': {
                'internal_radius_default': 90.0,
                'collision_margin': 2.0,
                'exclusion_radius': 5.0,
                'tolerance': 2.0,
                'max_violation_threshold': 0.10,
                'min_lines_threshold': 10000
            },
            'engines': {
                'packmol': {
                    'executable': 'packmol',
                    'timeout': 300
                },
                'pymol': {
                    'headless': True,
                    'quiet': True
                }
            },
            'io': {
                'temp_dir': './temp',
                'cleanup_temp': True,
                'default_capsid': 'capside.pdb',
                'default_enzyme': 'enzima.pdb'
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'web': {
                'port': 5001,
                'host': '0.0.0.0'
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto.

        Args:
            key: Clave en notación de punto (ej: 'packing.tolerance')
            default: Valor por defecto si la clave no existe

        Returns:
            Valor de configuración o default si no existe

        Examples:
            >>> config = ConfigManager()
            >>> config.get('packing.tolerance')
            2.0
            >>> config.get('packing.collision_margin')
            2.0
            >>> config.get('no.existe', 'valor_default')
            'valor_default'
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtiene una sección completa de configuración.

        Args:
            section: Nombre de la sección (ej: 'packing', 'engines')

        Returns:
            Diccionario con la configuración de la sección
        """
        return self._config.get(section, {})

    def get_engine_config(self, engine: str) -> Dict[str, Any]:
        """
        Obtiene la configuración específica de un motor.

        Args:
            engine: Nombre del motor ('packmol', 'pymol')

        Returns:
            Diccionario con configuración del motor
        """
        return self.get(f'engines.{engine}', {})

    def reload(self):
        """
        Recarga la configuración desde el archivo.
        Útil si el archivo ha sido modificado durante ejecución.
        """
        self._config = self._load_config()

    def __str__(self) -> str:
        """
        Representación string del gestor de configuración.
        """
        return f"ConfigManager(config_path='{self.config_path}')"

    def __repr__(self) -> str:
        """
        Representación para debugging.
        """
        return self.__str__()