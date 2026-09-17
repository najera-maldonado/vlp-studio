#!/bin/bash
# Ejecutor de análisis individual
# Estructura: analisis_individual/enzimas/enzima#/{rmsf,sasa,rmsd}
#            analisis_individual/capside/{ryg,rmsd}

echo "================================================================================"
echo "EJECUTANDO ANÁLISIS INDIVIDUAL"
echo "================================================================================"

cd analisis_individual

# Análisis de enzimas

echo "🧬 Analizando enzima 1..."
cd enzimas/enzima1

echo "  📊 RMSF..."
cd rmsf && cpptraj -i rmsf.cpptraj && cd ..

echo "  🔍 SASA..."
cd sasa && cpptraj -i sasa.cpptraj && cd ..

echo "  📈 RMSD..."
cd rmsd && cpptraj -i rmsd.cpptraj && cd ..

cd ../..

# Análisis de cápside
echo "🏗️ Analizando cápside..."
cd capside

echo "  ⚪ Radio de giro..."
cd ryg && cpptraj -i ryg.cpptraj && cd ..

echo "  📈 RMSD..."
cd rmsd && cpptraj -i rmsd.cpptraj && cd ..

cd ..

echo "✅ Análisis completado"
echo "📁 Resultados organizados en:"
echo "   - enzimas/enzima#/rmsf/enzima#_rmsf_*.dat"
echo "   - enzimas/enzima#/sasa/enzima#_sasa.dat"
echo "   - enzimas/enzima#/rmsd/enzima#_rmsd_*.dat"
echo "   - capside/ryg/capside_ryg.dat"
echo "   - capside/rmsd/capside_rmsd_*.dat"
