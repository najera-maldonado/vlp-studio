# Auditoría empírica — conversión coarse-grained (SIRAH) y motor `sustratinaitor`

> **Fecha:** 2026-10-04 · **Alcance:** las dos conversiones a CG del repo (PackMan y sustratinaitor),
> la construcción del sustrato GYE, el empaquetado alrededor de la cápside y la decisión abierta
> CIENCIA-2. **Método:** Python 3 + NumPy sobre los PDB commiteados, más reproducción real de la
> receta con `pdb2pqr 3.7.1` y `cgconv.pl` (SIRAH 2.3, incluido en el repo). **No se cambió
> código.** El script de verificación está en `herramientas/auditoria_cg.py` (solo lectura).
>
> Regla seguida (REVISION_MOTORES.md): juicio propio primero; el archivo sellado se leyó al final
> solo para cross-check (§7).

---

## 0. Veredicto en cuatro líneas

1. **La conversión CG de sustratinaitor (`1_capside/3J7L_cg.pdb`) está bien hecha.** 131 820 beads,
   28 620 residuos, **cero** fallas contra `amino.lib`, 180 TER conservados, beads derivados de
   hidrógenos presentes en el 100 % de Ser/Thr/Cys/Trp, enlaces GO–GN 2.24 ± 0.01 Å.
2. **Su receta es exactamente `pdb2pqr --ff=AMBER` → `cgconv.pl` aplicada a la cápside sola, con sus
   TER, antes de empaquetar.** Reproducida aquí sobre `PackMan/.../capside.pdb`: el archivo
   resultante es **idéntico byte a byte** (mismo md5) al del autor.
3. **PackMan falla porque ejecuta esos mismos dos pasos en el orden y la forma equivocados**: su
   `run_maestro.sh` salta pdb2pqr (pierde 1 bead en cada Ser/Thr/Cys/Trp) y pasa a `cgconv.pl` la
   salida de Packmol, que no tiene TER (180 cadenas fundidas en una). Portar la receta es trivial.
4. **El resto de sustratinaitor no es simulable tal cual.** El empaquetado `3J7L-GYE.pdb` también
   perdió los 180 TER; el GYE empaquetado es all-atom (144 átomos, 89 H) bajo un protocolo SIRAH de
   20 fs sin SHAKE; el GYE "CG" de 17 beads no tiene topología en ninguna librería SIRAH y su
   geometría no es CG (beads a 1.4 Å). CIENCIA-2 no es una decisión libre: la opción híbrida está
   descartada por física; quedan "parametrizar GYE en SIRAH" o "sacar el sustrato de la MD CG".

---

## 1. Conversión CG de sustratinaitor: `3J7L_cg.pdb`

### 1.1 Qué es la cápside

- 180 subunidades (T = 3): 60 cadenas de 149 residuos (41–189) y 120 de 164 (26–189).
- La secuencia es **idéntica (149/149) a la cadena A de `nanocapsule-mvp/Input/Capsides/BMV_IJS9`**:
  es la proteína de cápside de **Brome Mosaic Virus**; 3J7L es su modelo de crio-EM. No es P22 ni
  CCMV (CCMV 1CWP da 13/148 por posición).
- Coordenadas originales (centroide en 207.9, 207.9, 207.9), sin hidrógenos en el all-atom fuente
  (`PackMan/.../empaquetador/capside.pdb`: 216 780 átomos pesados, 0 H, 180 TER).

### 1.2 Beads por residuo contra `amino.lib` (SIRAH 2.3)

| residuo SIRAH | n residuos | beads/res observado | esperado (`amino.lib`) | fallas |
|---|---:|---:|---:|---:|
| sA | 4 920 | 3 | 3 | 0 |
| sV | 3 060 | 4 | 4 | 0 |
| sL | 2 820 | 4 | 4 | 0 |
| sK | 1 980 | 5 | 5 | 0 |
| sS | 1 980 | 5 | 5 | 0 |
| sE | 1 920 | 6 | 6 | 0 |
| sI | 1 380 | 4 | 4 | 0 |
| sG | 1 320 | 3 | 3 | 0 |
| sT | 1 260 | 5 | 5 | 0 |
| sP | 1 140 | 4 | 4 | 0 |
| sD | 1 080 | 6 | 6 | 0 |
| sR | 1 020 | 7 | 7 | 0 |
| sQ | 960 | 6 | 6 | 0 |
| sF, sY | 900 c/u | 6 | 6 | 0 |
| sHe | 540 | 6 | 6 | 0 |
| sN | 540 | 6 | 6 | 0 |
| sM | 360 | 4 | 4 | 0 |
| sW | 360 | 8 | 8 | 0 |
| sC | 180 | 5 | 5 | 0 |
| **total** | **28 620** | | | **0** |

La comparación es por **nombre de bead exacto**, no solo por conteo. No hay ningún residuo con
beads de más, de menos o mal nombrados.

### 1.3 Beads que SIRAH deriva de hidrógenos (la prueba de la protonación)

`sirah_prot.map` construye **BPG** a partir de `HG` (Ser, Thr, Cys) y **BPE** a partir de `HE1`
(Trp). Sin hidrógenos en la entrada esos beads no existen.

| residuo | residuos con el bead | distancia bead–átomo pesado |
|---|---|---|
| sS (BPG) | 1 980 / 1 980 | \|BOG–BPG\| = 1.000 Å (0.998–1.001) |
| sT (BPG) | 1 260 / 1 260 | ídem |
| sC (BPG) | 180 / 180 | \|BSG–BPG\| = 1.004 Å |
| sW (BPE) | 360 / 360 | \|BNE–BPE\| = 0.999 Å |

Distancias de 1.00 Å = longitud de enlace O–H / N–H: los beads están **sobre hidrógenos reales**,
no inventados. La entrada a `cgconv.pl` estaba protonada.

### 1.4 Registros TER y continuidad de cadena

| métrica | valor |
|---|---|
| TER / END | 180 / 1 (un TER por subunidad) |
| GC(i)–GC(i+1) dentro de cadena (n = 28 440) | media 3.784 Å, sd 0.066, min 2.790, max 3.873; **0** pares > 4.5 Å |
| GO(i)–GN(i+1) dentro de cadena (enlace SIRAH) | media 2.243 Å, sd 0.008 (2.214–2.274) |
| saltos de numeración dentro de cadena | 0 (no hay loops faltantes) |
| GC–GC cruzando un TER (n = 179) | 24.7 – 215.1 Å (media 85.7): **sin los TER tleap crearía 179 enlaces de esa longitud** |
| pares GC–GC en [2.5, 3.0) Å | 120 = 60 × (142→Gly143) + 60 × (187→Tyr188): péptidos *cis* heredados del modelo 3J7L (crio-EM 3.8 Å), no un error de conversión |

### 1.5 Correspondencia bead a bead con el all-atom de PackMan

Comparando residuo a residuo `capside.pdb` (PackMan) con `3J7L_cg.pdb`:

- Mismos 28 620 residuos, misma secuencia por segmento tras mapear AA→SIRAH.
- **GC = CA, GN = N, GO = O con desviación máxima 0.0000 Å** en los 28 620 residuos; Lys CG/CE,
  Ser OG, Trp NE1/CZ2: 0.0000 Å.
- Excepciones, todas con firma de **pdb2pqr**: 120 Asn y 134 Gln con la amida volteada (BOD/BND
  intercambiados = *flips* del optimizador de puentes de hidrógeno) y 30 Arg177 con CZ desplazado
  ≤ 1.40 Å (*debump*). Sin pdb2pqr (cgconv directo) esos flips no aparecen (0/21 en la prueba).
- Todas las His son **sHe** (540): pdb2pqr sin `--ffout` escribe `HIS` y `cgconv.pl` manda `HIS`
  a sHe por defecto (ver 1.7).

### 1.6 Reproducción de la receta (prueba definitiva)

```bash
# entorno: pdb2pqr 3.7.1 (el autor usó 3.6.1, ver 2_ligando_GYE/GYE.log), perl 5.38,
# cgconv.pl v15 del bundle sirah_x2.3_24-07.amber que ya está en PackMan.v.1.2
pdb2pqr --ff=AMBER PackMan.v.1.2/archivos_dm_cg/empaquetador/capside.pdb full.pqr   # 84 s
perl PackMan.v.1.2/archivos_dm_cg/sirah_x2.3_24-07.amber/tools/CGCONV/cgconv.pl -i full.pqr -o full_cg_repro.pdb
md5sum sustratinaitor/1_capside/3J7L_cg.pdb full_cg_repro.pdb
# 1d038b4bbe9c1d4dc80a0ebcc83408e6  ambos  -> IDÉNTICOS (131 820 ATOM, 180 TER, 1 END)
```

PQR intermedio: 439 620 átomos (222 840 H añadidos), 180 TER. Es decir, **la receta son los dos
comandos que ya están escritos en `PackMan.v.1.2/convert_to_cg.sh`**, aplicados a la cápside sola
y antes de Packmol. No hay ningún paso oculto.

### 1.7 Dos matices científicos de la receta (no invalidan la cápside, sí importan para la enzima)

Probado sobre un bloque cápside + enzima (`capside_1enzimas_*.pdb`, última copia de cadena C + GCase):

| opción pdb2pqr | Cys de puente S–S | His | efecto en CG |
|---|---|---|---|
| `--ff=AMBER` (la del autor) | quedan `CYS` **sin HG** | todas `HIS` | las 4 Cys del puente salen como **sC incompletas (4 beads)**; tleap añadiría un BPG arbitrario y no habría puente; His → sHe por defecto |
| `--ff=AMBER --ffout=AMBER` | `CYX` ×4 | HID 18 / HIE 4 | **sX** ×4 (4 beads, correcto; falta `bond` en tleap); His con tautómero elegido por el optimizador |
| + `--titration-state-method=propka --with-ph=7.0` | `CYX` ×4 | HID 17 / HIE 4 / HIP 1 | además 4 Asp/Glu protonados (ASH/GLH) según pKa predicho |

- **Cápside:** sin puentes disulfuro (distancia mínima SG–SG entre sus 180 Cys = 22.8 Å), así que
  `3J7L_cg.pdb` no sufre el problema de las Cys. Sí tiene las 540 His en tautómero por defecto.
- **Enzima (GCase, `enzima.pdb`):** 7 Cys, **dos puentes** (4–16 y 18–23 a 2.04 Å). Con la receta
  tal cual los perdería. Para la enzima la receta debe llevar `--ffout=AMBER`.

---

## 2. Qué hace mal PackMan y cómo portar la receta

### 2.1 Diagnóstico empírico de la ruta de PackMan

| archivo / paso | observado | consecuencia |
|---|---|---|
| `empaquetador/capside.pdb` | 216 780 átomos pesados, **0 H**, 180 TER | entrada válida para pdb2pqr |
| `capside_recentrada.pdb` (PyMOL `save`) | mismos átomos, **3 TER**: PyMOL reordena por chain ID (A×60, B×60, C×60) | 177 pares de residuos consecutivos a 25–215 Å sin TER |
| `enzima.pdb` | 497 res, 3 973 átomos, 0 H, sin huecos; 86 Ser/Thr/Cys/Trp; 2 puentes S–S | necesita protonación y CYX |
| `capside_1enzimas_*.pdb` (salida Packmol) | 220 753 átomos, **0 TER**, **103 454 seriales hexadecimales**, 0 H, 3 866 Ser/Thr/Cys/Trp | lo que `run_maestro.sh` manda a cgconv |
| `run_maestro.sh` paso 3 | `cgconv.pl` **directo, "salta pdb2pqr"** | ver fila siguiente |
| cgconv sin H (probado, 3 cadenas) | 2 004 beads en vez de 2 067: faltan **57 BPG + 6 BPE** | ≈ 3 866 beads faltantes en el sistema completo; tleap los "añade" en posición arbitraria |
| cgconv sobre salida Packmol (probado) | **TER = 0** | tleap enlaza 180 uniones de 25–215 Å (179 entre subunidades + cápside→enzima) |
| `convert_to_cg.sh` (pdb2pqr → cgconv) | pdb2pqr **aborta** con los seriales hex (`ValueError: '349F5'`) | solo funciona si antes se corre `fix_pdb_serial.py` (existe, pero ningún script lo llama) |
| `fix_pdb_serial.py` → pdb2pqr → cgconv (probado) | pdb2pqr **sí** separa cadenas al bajar la numeración (189→41, 189→1): 2 TER, 2 H3, 2 OXT; 3 166 beads = 754 (copia de cadena C) + 2 412 (enzima), con BPG/BPE presentes; las 4 Cys del puente S–S quedan incompletas salvo con `--ffout=AMBER` (§1.7) | ruta viable como alternativa, pero depende de esa heurística |
| `setup_universal_md.sh`, `setup_1_1o.sh` | usan `gensystem_template.leap` y `run_MD_template.sh`, que **no existen**; el primero sugiere `pdb4amber` para "generar CG" (no convierte nada) | scripts rotos / instrucciones engañosas |
| `run_maestro.sh` paso 6 | llama `analisis/ejecutar_analisis_cpptraj.sh`, inexistente | — |
| `gensystem.leap` | `addIonsRand protein NaW 0` con comentario "0.15M NaCl" | carga neta de la cápside = 0 (sD −1080, sE −1920, sK +2040, sR +960): **no se añade ningún ion** |

Conclusión: la "topología inválida por falta de hidrógenos y pérdida de TER" se confirma **para la
ruta que realmente automatiza el motor** (`run_maestro.sh`). La ruta documentada
(`convert_to_cg.sh`) tendría los H y recuperaría las cadenas, pero hoy aborta por los seriales hex.

### 2.2 Receta a portar (orden que sustratinaitor sí respetó)

El principio: **protonar y convertir cada componente por separado, con sus TER, y empaquetar
después**. Es lo que hizo sustratinaitor con la cápside.

1. **Cápside:** `pdb2pqr --ff=AMBER --ffout=AMBER capside.pdb capside.pqr` →
   `cgconv.pl -i capside.pqr -o capside_cg.pdb`. Esperado: 131 820 beads, 180 TER. (Sin `--ffout`
   el resultado es byte-idéntico a `3J7L_cg.pdb`; con `--ffout` cambia solo el tautómero de las
   540 His — decisión científica menor, documentarla.)
2. **Enzima:** mismo par de comandos sobre `enzima.pdb` → `enzima_cg.pdb`. Esperado: 497 residuos,
   1 TER, **4 sX** (Cys 4, 16, 18, 23) y 2 412 beads. Opcional: `--titration-state-method=propka
   --with-ph=7.0` si se quiere protonación por pKa (cambia 4 Asp/Glu y 1 His en la prueba).
3. **Centrar la cápside CG** con una traslación que respete líneas y TER (NumPy: restar el
   centroide; **no** PyMOL `save`, que reordena y colapsa los TER), o dejar que Packmol la centre con
   `center` + `fixed 0. 0. 0. 0. 0. 0.` como en `sustratinaitor/3_empaquetado_packmol/packmol_input.inp`.
4. **Packmol sobre los CG** (la cápside fija, N enzimas `inside sphere` con el radio de
   `1calcula_radio_interno.py`, `seed` fijo, `add_amber_ter`). Es más rápido que en all-atom y la
   tolerancia 2.0 Å ya es la de la referencia.
5. **Reinsertar los TER** que Packmol borra dentro de la cápside: regla "TER cuando baja el número
   de residuo o cambia la clase de molécula". Probado sobre `3J7L-GYE.pdb`: devuelve exactamente los
   379 TER esperados (179 + 1 + 199). Alternativa equivalente: no usar la cápside de la salida de
   Packmol, sino concatenar `capside_cg.pdb` centrada + cada enzima extraída de la salida con su TER.
6. **Validar antes de tleap** con `herramientas/auditoria_cg.py` (o sus chequeos): beads por
   residuo = `amino.lib`, BPG/BPE presentes, TER = 180 + N, GC–GC 3.78 ± 0.07 Å, GO–GN 2.24 Å,
   0 pares consecutivos sin TER > 4.5 Å.
7. **tleap** (`leaprc.sirah`): `loadpdb`, **`bond` de los puentes disulfuro de cada copia de la
   enzima** (`bond sys.<i>.BSG sys.<j>.BSG`; índices = 28 620 + offset de copia + resi), `charge`,
   iones **explícitos** para 0.15 M (como en el tutorial 5 de SIRAH: `addIonsRand sys NaW n ClW n`),
   `solvateOct ... WT4BOX`. Revisar `leap.log`: 0 "Added missing", 0 "Created a new atom".
8. Retirar de `run_maestro.sh` el "salta pdb2pqr"; corregir la referencia a `pdb4amber`; crear o
   eliminar las plantillas inexistentes; y, cuando se decida CIENCIA-3, los `heat*.in` all-atom.

Coste estimado: medio día de scripting + ~2 min de cómputo (pdb2pqr 84 s para la cápside). No toca
ningún motor de terceros.

---

## 3. Empaquetado de sustratinaitor: `3_empaquetado_packmol/3J7L-GYE.pdb`

### 3.1 Integridad del archivo

| métrica | valor |
|---|---|
| átomos | 160 620 = 131 820 (cápside CG) + 200 × 144 (GYE **all-atom**) |
| cápside | idéntica a `3J7L_cg.pdb` trasladada (−207.9, −207.9, −207.9); nombres y numeración preservados |
| **TER** | **0** (Packmol no los conserva) → 179 uniones entre subunidades de 25–215 Å + cápside→GYE que tleap enlazaría |
| seriales | 51 951 líneas en hexadecimal (> 99 999) |
| GYE | resi 1–200, chain A, 89 H por copia |
| Packmol | v21.0.1, `seed 1234567`, tolerancia 2.0, 133 s, "Success", 0 violaciones; `packmol.log` es una copia truncada de `packmol_run.log` |

El archivo que alimenta `4_ensamblaje_y_simulacion/gensystem.leap` tiene por tanto **el mismo
defecto de TER que PackMan**, aunque la cápside de partida estuviera bien. La reinserción por regla
(§2.2 paso 5) lo corrige.

### 3.2 Dónde quedaron realmente las 200 copias ("alrededor" es una verdad a medias)

Perfil radial de la cápside desde su centroide: min 89.5 Å, p1 96.4, mediana 118.9, p99 140.2,
max 142.6 Å. Extensión cartesiana ±139.6/136.0/141.5 Å; caja Packmol ±150.3/147.2/152.0 Å.

| posición del centro de masa del GYE | copias |
|---|---:|
| lumen (r < 96.4 Å) | 49 |
| dentro del cascarón / poros (96.4–140.2 Å) | 23 |
| exterior (r > 140.2 Å) | 128 |
| con **todos** sus átomos en el lumen | 30 |
| con todos sus átomos fuera | 101 |
| a caballo del cascarón | 69 |

- Radio del COM: 18.8 – 225.2 Å (mediana 150.0). Distancia mínima GYE–cápside 2.00 Å (la
  tolerancia se respeta); 62 copias en contacto (≤ 4 Å), 60 a más de 20 Å.
- El 57 % del volumen de la caja está fuera de la esfera de la cápside y el 14 % en el lumen, y
  Packmol llena ambos: **una cuarta parte del sustrato queda dentro de la cápside**. Si la pregunta
  científica es el cruce del poro (Puerta 1), hace falta `outside sphere` (cascarón explícito); si es
  el sustrato ya encapsulado, `inside sphere` con el radio interno. La geometría actual mezcla ambos
  escenarios.
- Concentración nominal: 12.3 mM en la caja (88 mM si estuvieran todas en el lumen): alta pero
  defendible para muestreo; documentar el criterio de "200".
- Curiosidad sin consecuencia: dos GYE con COM a 1.6 Å (moléculas de 47 Å cruzadas en X).

---

## 4. Construcción del sustrato (`2_ligando_GYE/`)

### 4.1 Lo que se empaquetó: `GYE.pdb` (all-atom)

144 átomos (C46 H89 N1 O8; 55 pesados), carga total 0.002 e (AM1-BCC), tipos GAFF2, `GYE.frcmod`
con solo dos impropios. `convert.leap` lo carga con `leaprc.gaff2` y guarda `GYE.off`/`GYE.pdb`.
`GYE.log` muestra que el autor intentó pdb2pqr 3.6.1 sobre GYE (falla, lógico: no es proteína).
Todo esto es **parametrización all-atom**; ningún paso produce algo CG.

### 4.2 Lo que no se usó: `GYE_cg_manual.pdb` (17 "beads")

| bead | átomo más cercano | distancia |
|---|---|---:|
| 1–11 (GC, GO, GC, GO, BGL, BCE, BC1–BCT) | C25, O3, C26, C24, N1, C22, C28, C33, C35, C39, C43 | **0.00 Å** (son átomos individuales, no centros de masa) |
| 12–17 (BF1–BF6) | C3, C6, C10, C14, C18, C20 | 0.26–0.74 Å (≈ COM de 4 C, correcto) |

- Distancias entre beads consecutivos de la cabeza: **1.43, 1.44, 1.39 Å** (longitudes de enlace
  atómico; SIRAH usa 3–5 Å). 6 de 17 beads tienen un vecino a < 2 Å.
- Las 17 líneas tienen la columna de cadena corrida (chain en col 23): **PDB inválido**.
- Nombres de bead tomados de SIRAH (GC/GO del esqueleto proteico, BGL/BCE de lípidos), pero **no
  existe residuo `GYE` en ninguna `.lib` de SIRAH**: sin topología, sin cargas, sin parámetros
  enlazantes. La frase "Compatible with SIRAH force field topology generation" del README es falsa.
- Inventario real de SIRAH 2.3 (bundle del repo): lípidos CMM/CPP/CPO/EPO/SPO (= DMPC, DPPC, POPC,
  POPE, POPS) y fragmentos xPC/xPE/xPS/xMY/xPA/xOL; glicanos: 18 residuos de **Fuc, Man, Gal, GlcNAc,
  Neu5Ac**. **No hay glucosa ni ceramida/esfingolípido.** "Todo CG" exige parametrizar.

### 4.3 Etapa 4 tal como está escrita

- `gensystem.leap` guarda `3J7L-GYE_cg.prmtop/.ncrst`; `run_MD.sh` busca
  `3J7L-GYE_cg-WAT.prmtop/.ncrst`: **nombres distintos**, el pipeline no arranca aunque tleap funcione.
- `em1/em2/eq1/eq2_WT4.in` no están en la carpeta (vienen de PackMan: `eq*.in` con `nstlim=500`,
  10 ps, rotulados "15 ns"/"35 ns"; `em1` sin restricciones, el tutorial SIRAH usa `@GN,GO` a 2.4).
- `addIonsRand protein NaW 0`: con carga neta 0 no añade iones; el comentario promete 0.15 M.
- `source leaprc.sirah` + `source leaprc.gaff2` + `loadmol2 GYE.mol2`: mezcla deliberada de campos
  de fuerza (ver §5).

---

## 5. CIENCIA-2: coherencia de resolución

**No es una decisión aplazable entre dos opciones válidas; una está muerta y la otra cuesta.**

**Por qué el híbrido commiteado (cápside CG + GYE all-atom GAFF2 + agua WT4) no corre:**
1. `3J7L-GYE.pdb` no tiene TER (§3.1): tleap crearía 180 enlaces de hasta 215 Å. Esto por sí solo
   destruye el sistema en la minimización.
2. El protocolo SIRAH integra a **dt = 20 fs sin SHAKE** (`ntc=1, ntf=1`, correcto para beads). Los
   89 H de cada GYE vibran a ~10 fs: la integración explota. Bajar a 2 fs anula la ventaja CG.
3. Los cruces GAFF2 × SIRAH (LJ por Lorentz–Berthelot, cargas AM1-BCC frente a las cargas efectivas
   de SIRAH y su `LJoff.frcmod`) no están parametrizados ni validados. Los multiescala soportados
   por SIRAH son proteína AA en agua CG (vía `wt4tip3p`) y ADN AA/CG, no ligando AA en proteína CG.
4. Además, ninguna de las cuatro verificaciones anteriores se ha hecho porque la etapa 4 nunca se
   ejecutó, y con los nombres de archivo actuales no podría.

**Opciones reales:**

| opción | qué implica | coste | recomendación |
|---|---|---|---|
| **A. Todo CG con un GYE SIRAH de verdad** | construir el residuo: cabeza con el patrón de 6 beads de los glicanos SIRAH usando β-Gal (`BL0`) como proxy de β-Glc (epímero en C4; a resolución CG la diferencia es una orientación de hidroxilo) o pedirlo al grupo SIRAH; cola 24:0 = 6 beads tipo `xMY/xPA` (3.5–4 C/bead), esfingosina 18:1 = 5 beads con un bead insaturado tipo `xOL`; enlazante amida/glicosídico por analogía; cargas efectivas SIRAH; validar distribuciones enlace/ángulo contra la MD all-atom del GYE (que ya existe con GAFF2) | 2–4 semanas de alguien que conozca SIRAH; mini-proyecto con publicación propia | viable si el sustrato **debe** estar en la MD CG de la cápside |
| **B. Sacar el GYE de la MD CG** | Puerta 4 (¿sobrevive?) se corre cápside + enzima en SIRAH (PackMan reparado, §2.2); la física del sustrato (cruce del poro, unión) se trata **all-atom** en sistemas pequeños: poro + GYE con PMF/SMD, sitio activo + GYE, como ya figura en PENDIENTES ("all-atom del sitio activo", "steered MD") | cero parametrización nueva; reutiliza `GYE.mol2/.frcmod` tal cual | **recomendada**: coherente con el embudo y sin ciencia sin validar |
| C. Híbrido actual | — | — | **descartar** (puntos 1–3) |
| D. Todo all-atom con cápside entera | ~5 M átomos solvatados | inviable con la GPU disponible | no |

Si se elige A, `GYE_cg_manual.pdb` **no** sirve de punto de partida (§4.2): hay que rehacer el mapeo
con `cgconv.pl` y un `.map` propio (CMASS de grupos de 3–4 átomos pesados), que es justo el camino
que el autor abandonó ("GYE_custom.map … not used due to atom type issues").

---

## 6. Hallazgos menores y de documentación

- `sustratinaitor/README.md` y `EXPLICACION.md` dicen "cápside 3J7L (~131.820 beads)" sin nombrar
  el virus: es **BMV**. Conviene decirlo, porque el Studio tiene BMV_1JS9 en su biblioteca y la
  cápside de PackMan es la misma molécula.
- `README_conversion_gye_cg.md`: afirma compatibilidad SIRAH y mapeo por centros de masa; ambas
  cosas son falsas para los beads 1–11.
- `sustratinaitor/CHANGELOG.md` y `ESTADO.md §4` describen bien el mismatch de resolución, pero no
  la pérdida de TER ni la geometría inválida del GYE CG.
- El bundle SIRAH del repo se llama `x2.3_24-07`, su `leaprc` dice "2.3 Nov 2023" y su `0README`
  "March 2025": anotar la versión exacta usada en la tesis.
- `herramientas/auditoria_cg.py` deja constancia reproducible de todos los números de este informe.

---

## 7. Cross-check con `REVISION_MOTORES_hallazgos_sellados.md` (leído al final)

| sospecha sellada | veredicto |
|---|---|
| sustratinaitor: GYE empaquetado all-atom (144), CG de 17 beads huérfano | **Confirmado** y ampliado: el híbrido es inviable por integración y por TER, no solo "incoherente" |
| sustratinaitor: "0.15M NaCl" vs `addIonsRand NaW 0` | **Confirmado** y cuantificado: carga neta 0, no se añade ningún ion (igual en PackMan) |
| PackMan: `heat*.in` all-atom sobre CG (CIENCIA-3) | No era el objetivo de esta pasada; coincide con la lectura de los `.in` |
| "Auditoría previa": PackMan produce topología inválida por falta de H y pérdida de TER | **Confirmado para `run_maestro.sh`** (cgconv directo). **Matiz nuevo:** la ruta `convert_to_cg.sh` sí protonaría y pdb2pqr recupera las cadenas al bajar la numeración, pero **aborta con los seriales hexadecimales** de Packmol salvo que se corra antes `fix_pdb_serial.py`; además PyMOL ya había colapsado los TER a 3 |

Lo que la pasada previa **no** vio: que `3J7L_cg.pdb` es reproducible byte a byte con dos comandos;
que la salida de Packmol de sustratinaitor también carece de TER; que la receta del autor pierde los
puentes disulfuro de la enzima si se aplica sin `--ffout=AMBER`; que el GYE CG manual tiene
geometría atómica; y que un cuarto del "sustrato alrededor" está dentro de la cápside.

---

## 8. Plan de reparación (ordenado por coste/beneficio)

### P0 — Desbloquear la MD de Puerta 4 (PackMan). Barato, sin ciencia nueva.
1. Reemplazar el paso 3 de `run_maestro.sh` por la receta de §2.2 (pdb2pqr `--ff=AMBER
   --ffout=AMBER` → cgconv) **por componente y antes de Packmol**. Eliminar el "salta pdb2pqr".
2. Sustituir el recentrado con PyMOL por traslación NumPy o por `center` de Packmol; añadir
   `add_amber_ter` y un post-proceso que reinserte TER por regla; verificar TER = 180 + N.
3. Añadir en `gensystem.leap`: `bond` de los dos puentes S–S por copia de enzima; iones explícitos
   a 0.15 M (NaW/ClW); revisar `leap.log` (0 átomos añadidos/creados).
4. Cablear `herramientas/auditoria_cg.py` (o sus chequeos) como paso de validación previo a tleap;
   criterio de aceptación: 0 fallas contra `amino.lib`, 0 uniones sin TER > 4.5 Å, BPG/BPE al 100 %.
5. Arreglar referencias rotas: `gensystem_template.leap`, `run_MD_template.sh`,
   `ejecutar_analisis_cpptraj.sh`, mensaje de `pdb4amber`. Encadenar `fix_pdb_serial.py` si se
   mantiene la ruta all-atom como alternativa.
6. Prueba de humo obligatoria antes de producción: em1 con `restraintmask='@GN,GO'` (tutorial 5),
   10 ps de eq1 a 20 fs; si explota, el problema es de topología, no de protocolo.

### P1 — sustratinaitor: higiene inmediata (independiente de CIENCIA-2)
7. Reinsertar TER en `3J7L-GYE.pdb` (si se conserva) y unificar nombres entre `gensystem.leap` y
   `run_MD.sh`; copiar o referenciar los `.in`; corregir el README del GYE CG y el formato de
   `GYE_cg_manual.pdb` o retirarlo; nombrar BMV.
8. Decidir el escenario geométrico y reflejarlo en Packmol: `outside sphere` (sustrato fuera, Puerta 1)
   o `inside sphere` (sustrato dentro). Documentar el criterio del número de copias.

### P2 — CIENCIA-2 (decisión de Lucio, con esta evidencia)
9. **Recomendación: opción B** (sustrato fuera de la MD CG; física del sustrato en all-atom
   pequeño). Si se elige A, abrir sub-proyecto "GYE-SIRAH" con el camino de §5 y criterio de
   validación contra la MD all-atom del GYE.
10. Registrar en ESTADO §4b que la opción híbrida queda descartada por evidencia (§5, puntos 1–3).

### P3 — Decisiones de protonación (afectan a ambas cápsides CG)
11. Fijar la política de pdb2pqr (`--ffout=AMBER`; con o sin propka a pH 7) y regenerar
    `3J7L_cg.pdb`/`capside_cg.pdb` con ella. Cambia el tautómero de 540 His; documentar en CHANGELOG
    de ambos motores. La receta ya es reproducible, así que el cambio es trazable.

### Cómo reproducir esta auditoría
```bash
pip install numpy pdb2pqr                       # pdb2pqr 3.7.1 usado aquí
python3 herramientas/auditoria_cg.py            # secciones 1-5; ~1 min (la 3b hace 28 800×131 820 distancias)
python3 herramientas/auditoria_cg.py 1 2        # solo cápside y correspondencia
# receta y comparación byte a byte: ver §1.6
```
