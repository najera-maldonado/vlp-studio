#!/bin/bash
# Script para copiar los archivos de grafiqueo a sus directorios correspondientes

echo "================================================================================"
echo "COPIANDO SCRIPTS DE GRAFIQUEO A SUS DIRECTORIOS CORRESPONDIENTES"
echo "================================================================================"

# Directorio base
BASE_DIR="analisis_individual"
GRAFIQUEO_DIR="grafiqueo"

# Verificar que existan los directorios
if [ ! -d "$BASE_DIR" ]; then
    echo "❌ Error: No existe el directorio $BASE_DIR"
    exit 1
fi

if [ ! -d "$GRAFIQUEO_DIR" ]; then
    echo "❌ Error: No existe el directorio $GRAFIQUEO_DIR"
    exit 1
fi

echo "📁 Directorios encontrados:"
echo "   - $BASE_DIR/"
echo "   - $GRAFIQUEO_DIR/"
echo ""

# Contador de copias
COPIADOS=0

# Copiar scripts para enzimas
echo "🧬 COPIANDO SCRIPTS PARA ENZIMAS..."
ENZIMAS=$(find $BASE_DIR/enzimas -maxdepth 1 -type d -name "enzima*" | wc -l)
echo "   Enzimas detectadas: $ENZIMAS"

for enzima_dir in $BASE_DIR/enzimas/enzima*/; do
    if [ -d "$enzima_dir" ]; then
        enzima_name=$(basename "$enzima_dir")
        echo "   📊 $enzima_name:"

        # Copiar a rmsd/
        if [ -d "${enzima_dir}rmsd" ]; then
            cp "$GRAFIQUEO_DIR/enzimas/plot_rmsd.py" "${enzima_dir}rmsd/"
            echo "     ✅ plot_rmsd.py → ${enzima_name}/rmsd/"
            ((COPIADOS++))
        fi

        # Copiar a rmsf/
        if [ -d "${enzima_dir}rmsf" ]; then
            cp "$GRAFIQUEO_DIR/enzimas/plot_rmsf.py" "${enzima_dir}rmsf/"
            echo "     ✅ plot_rmsf.py → ${enzima_name}/rmsf/"
            ((COPIADOS++))
        fi

        # Copiar a sasa/
        if [ -d "${enzima_dir}sasa" ]; then
            cp "$GRAFIQUEO_DIR/enzimas/plot_sasa.py" "${enzima_dir}sasa/"
            echo "     ✅ plot_sasa.py → ${enzima_name}/sasa/"
            ((COPIADOS++))
        fi
    fi
done

echo ""

# Copiar scripts para cápside
echo "🏗️ COPIANDO SCRIPTS PARA CÁPSIDE..."
if [ -d "$BASE_DIR/capside" ]; then
    # Copiar a ryg/
    if [ -d "$BASE_DIR/capside/ryg" ]; then
        cp "$GRAFIQUEO_DIR/capside/plot_ryg.py" "$BASE_DIR/capside/ryg/"
        echo "   ✅ plot_ryg.py → capside/ryg/"
        ((COPIADOS++))
    fi

    # Copiar a rmsd/
    if [ -d "$BASE_DIR/capside/rmsd" ]; then
        cp "$GRAFIQUEO_DIR/capside/plot_rmsd.py" "$BASE_DIR/capside/rmsd/"
        echo "   ✅ plot_rmsd.py → capside/rmsd/"
        ((COPIADOS++))
    fi
else
    echo "   ⚠️ No se encontró directorio de cápside"
fi

echo ""

# Copiar script de comparación
echo "📈 COPIANDO SCRIPT DE COMPARACIÓN..."
if [ -d "$BASE_DIR/enzimas" ]; then
    cp "$GRAFIQUEO_DIR/comparacion/compara_enzimas_misma_capside.py" "$BASE_DIR/enzimas/"
    echo "   ✅ compara_enzimas_misma_capside.py → enzimas/"
    ((COPIADOS++))
else
    echo "   ⚠️ No se encontró directorio de enzimas"
fi

echo ""
echo "================================================================================"
echo "COPIA COMPLETADA"
echo "================================================================================"
echo "✅ Scripts copiados: $COPIADOS"
echo ""
echo "📁 ESTRUCTURA RESULTANTE:"
echo "   analisis_individual/"
echo "   ├── enzimas/"
for enzima_dir in $BASE_DIR/enzimas/enzima*/; do
    if [ -d "$enzima_dir" ]; then
        enzima_name=$(basename "$enzima_dir")
        echo "   │   ├── $enzima_name/"
        echo "   │   │   ├── rmsd/plot_rmsd.py"
        echo "   │   │   ├── rmsf/plot_rmsf.py"
        echo "   │   │   └── sasa/plot_sasa.py"
    fi
done
echo "   ├── capside/"
echo "   │   ├── ryg/plot_ryg.py"
echo "   │   └── rmsd/plot_rmsd.py"
echo "   └── compara_enzimas_misma_capside.py"
echo ""
echo "🚀 PARA EJECUTAR GRÁFICOS:"
echo "   # Gráfico individual:"
echo "   cd analisis_individual/enzimas/enzima1/rmsd && python plot_rmsd.py"
echo "   cd analisis_individual/capside/ryg && python plot_ryg.py"
echo ""
echo "   # Comparación entre enzimas:"
echo "   cd analisis_individual/enzimas && python compara_enzimas_misma_capside.py"
echo ""
echo "================================================================================"