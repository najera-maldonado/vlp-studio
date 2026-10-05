# RESULTADO NO VÁLIDO — no citar el 1.92 Å de esta carpeta

> Marcado el 2026-10-05 a partir de `AUDITORIA_PORO.md` (rama
> `claude/audit-poro-engine-giea7e`, hallazgos PORO-01, PORO-02 y PORO-03). La carpeta se
> conserva como evidencia; **no se borra ni se reutiliza**.

El perfil `hole/resultados/hole_profile.tsv` (347 puntos, radio mínimo 1.915 Å en
z = −15.38) es el único resultado de poro del repositorio y es el origen del "1.9 Å" de la
maqueta del Studio. Tres defectos independientes lo invalidan como medida del mutante
129HIS/132GLY y como medida del poro 5-fold de BMV:

1. **El "mutante" no está mutado.** `receptor.pdb` es byte-idéntico a `../WT.pdb`
   (md5 `d56a4e539c65c964ffe6fe7cd70a57d3` ambos). Las posiciones 129 y 132 siguen siendo
   SER y VAL en las cinco subunidades. El perfil es, por tanto, del tipo salvaje.
   ```bash
   cmp ../WT.pdb receptor.pdb && echo IDENTICOS
   awk '$1=="ATOM" && $3=="CA" && ($6==129||$6==132){print $6,$4}' receptor.pdb | sort | uniq -c
   ```
2. **No se regenera con los inputs commiteados.** `../../1crear_mutantes.pml` carga
   `poronatural.pdb` (trímero de CCMV, 3 574 átomos, cadenas A/B/C); `WT.pdb` es
   `modelos/BMV/poro5fold.pdb` centrado (5 735 átomos, cadenas A/B). Ejecutar hoy el
   pipeline procesa otra estructura.
3. **La geometría de HOLE no apunta al poro.** `pore_center.txt` (9.18, −3.88, 2.22) está a
   7.59 Å del eje de simetría C5; `pore_vector.txt` se desvía 19.29° de ese eje; la
   constricción trazada queda a 11.76 Å del eje real. El `hole_out.txt` no fija `rseed`
   (semilla por reloj: 2093611).

Qué haría válido un reemplazo: mutante verificado tras `apply()` (resn comprobado en los
cinco `segi`), eje y centro calculados por simetría (`BMV/poro5fold`, método del Studio,
0.00° de error), `rseed` fijo y sello de procedencia (md5 del PDB de entrada, `cpoint`,
`cvect`, `sample`, versión de HOLE). Tareas PO-1, PO-3, PO-4 y PO-7 de `HOJA_DE_RUTA.md`
(rama `claude/consolidate-audit-roadmap-k82rek`).

Si este 1.92 Å llegó a la tesis o a alguna figura, hay que emitir la corrección
correspondiente.
