##############################################################################
# MC-shell I/O capture file.
# Creation Date and Time:  Mon Mar  2 09:36:03 2026

##############################################################################
Hello world from PE 0
Vnm_tstart: starting timer 26 (APBS WALL CLOCK)..
NOsh_parseInput:  Starting file parsing...
NOsh: Parsing READ section
NOsh: Storing molecule 0 path mut_129HIS_132GLY.pqr
NOsh: Done parsing READ section
NOsh: Done parsing READ section (nmol=1, ndiel=0, nkappa=0, ncharge=0, npot=0)
NOsh: Parsing ELEC section
NOsh_parseMG: Parsing parameters for MG calculation
NOsh_parseMG:  Parsing sdens...
PBEparm_parseToken:  trying sdens...
NOsh_parseMG:  Parsing dime...
PBEparm_parseToken:  trying dime...
MGparm_parseToken:  trying dime...
NOsh_parseMG:  Parsing cglen...
PBEparm_parseToken:  trying cglen...
MGparm_parseToken:  trying cglen...
NOsh_parseMG:  Parsing fglen...
PBEparm_parseToken:  trying fglen...
MGparm_parseToken:  trying fglen...
NOsh_parseMG:  Parsing cgcent...
PBEparm_parseToken:  trying cgcent...
MGparm_parseToken:  trying cgcent...
NOsh_parseMG:  Parsing fgcent...
PBEparm_parseToken:  trying fgcent...
MGparm_parseToken:  trying fgcent...
NOsh_parseMG:  Parsing mol...
PBEparm_parseToken:  trying mol...
NOsh_parseMG:  Parsing lpbe...
PBEparm_parseToken:  trying lpbe...
NOsh: parsed lpbe
NOsh_parseMG:  Parsing bcfl...
PBEparm_parseToken:  trying bcfl...
NOsh_parseMG:  Parsing pdie...
PBEparm_parseToken:  trying pdie...
NOsh_parseMG:  Parsing sdie...
PBEparm_parseToken:  trying sdie...
NOsh_parseMG:  Parsing srfm...
PBEparm_parseToken:  trying srfm...
NOsh_parseMG:  Parsing chgm...
PBEparm_parseToken:  trying chgm...
MGparm_parseToken:  trying chgm...
NOsh_parseMG:  Parsing srad...
PBEparm_parseToken:  trying srad...
NOsh_parseMG:  Parsing swin...
PBEparm_parseToken:  trying swin...
NOsh_parseMG:  Parsing temp...
PBEparm_parseToken:  trying temp...
NOsh_parseMG:  Parsing calcenergy...
PBEparm_parseToken:  trying calcenergy...
NOsh_parseMG:  Parsing calcforce...
PBEparm_parseToken:  trying calcforce...
NOsh_parseMG:  Parsing write...
PBEparm_parseToken:  trying write...
NOsh_parseMG:  Parsing end...
MGparm_check:  checking MGparm object of type 1.
NOsh:  nlev = 4, dime = (97, 97, 97)
NOsh: Done parsing ELEC section (nelec = 1)
NOsh: Done parsing file (got QUIT)
Valist_readPQR: Counted 11418 atoms
Valist_getStatistics:  Max atom coordinate:  (52.165, 49.396, 39.457)
Valist_getStatistics:  Min atom coordinate:  (-55.337, -33.963, -63.144)
Valist_getStatistics:  Molecule center:  (-1.586, 7.7165, -11.8435)
NOsh_setupCalcMGAUTO(./src/generic/nosh.c, 1868):  coarse grid center = -1.586 7.7165 -11.8435
NOsh_setupCalcMGAUTO(./src/generic/nosh.c, 1873):  fine grid center = -1.586 7.7165 -11.8435
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1885):  Coarse grid spacing = 0.833333, 0.833333, 0.833333
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1887):  Fine grid spacing = 0.416667, 0.416667, 0.416667
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1889):  Displacement between fine and coarse grids = 0, 0, 0
NOsh:  2 levels of focusing with 0.5, 0.5, 0.5 reductions
NOsh_setupMGAUTO:  Resetting boundary flags
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1983):  starting mesh repositioning.
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1985):  coarse mesh center = -1.586 7.7165 -11.8435
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1990):  coarse mesh upper corner = 38.414 47.7165 28.1565
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 1995):  coarse mesh lower corner = -41.586 -32.2835 -51.8435
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 2000):  initial fine mesh upper corner = 18.414 27.7165 8.1565
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 2005):  initial fine mesh lower corner = -21.586 -12.2835 -31.8435
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 2066):  final fine mesh upper corner = 18.414 27.7165 8.1565
NOsh_setupCalcMGAUTO (./src/generic/nosh.c, 2071):  final fine mesh lower corner = -21.586 -12.2835 -31.8435
NOsh_setupMGAUTO:  Resetting boundary flags
NOsh_setupCalc:  Mapping ELEC statement 0 (1) to calculation 1 (2)
Vnm_tstart: starting timer 27 (Setup timer)..
Setting up PBE object...
Vpbe_ctor2:  solute radius = 68.1141
Vpbe_ctor2:  solute dimensions = 110.419 x 85.574 x 104.449
Vpbe_ctor2:  solute charge = 1
Vpbe_ctor2:  bulk ionic strength = 0
Vpbe_ctor2:  xkappa = 0
Vpbe_ctor2:  Debye length = 0
Vpbe_ctor2:  zkappa2 = 0
Vpbe_ctor2:  zmagic = 7042.98
Vpbe_ctor2:  Constructing Vclist with 75 x 75 x 75 table
Vclist_ctor2:  Using 75 x 75 x 75 hash table
Vclist_ctor2:  automatic domain setup.
Vclist_ctor2:  Using 1.9 max radius
Vclist_setupGrid:  Grid lengths = (118.578, 94.435, 113.677)
Vclist_setupGrid:  Grid lower corner = (-60.875, -39.501, -68.682)
Vclist_assignAtoms:  Have 3533473 atom entries
Vacc_storeParms:  Surf. density = 10
Vacc_storeParms:  Max area = 191.134
Vacc_storeParms:  Using 1936-point reference sphere
Setting up PDE object...
Vpmp_ctor2:  Using meth = 2, mgsolv = 1
Setting PDE center to local center...
Vpmg_fillco:  filling in source term.
fillcoCharge:  Calling fillcoChargeSpline2...
Vpmg_fillco:  filling in source term.
Vpmg_fillco:  marking ion and solvent accessibility.
fillcoCoef:  Calling fillcoCoefMol...
Vacc_SASA: Time elapsed: 1.204959
Vpmg_fillco:  done filling coefficient arrays
Vpmg_fillco:  filling boundary arrays
Vpmg_fillco:  done filling boundary arrays
Vnm_tstop: stopping timer 27 (Setup timer).  CPU TIME = 2.191684e+00
Vnm_tstart: starting timer 28 (Solver timer)..
Vnm_tstart: starting timer 30 (Vmgdrv2: fine problem setup)..
Vbuildops: Fine: (097, 097, 097)
Vbuildops: Operator stencil (lev, numdia) = (1, 4)
Vnm_tstop: stopping timer 30 (Vmgdrv2: fine problem setup).  CPU TIME = 1.822300e-02
Vnm_tstart: starting timer 30 (Vmgdrv2: coarse problem setup)..
Vbuildops: Galer: (049, 049, 049)
Vbuildops: Galer: (025, 025, 025)
Vbuildops: Galer: (013, 013, 013)
Vnm_tstop: stopping timer 30 (Vmgdrv2: coarse problem setup).  CPU TIME = 3.497270e-01
Vnm_tstart: starting timer 30 (Vmgdrv2: solve)..
Vnm_tstop: stopping timer 40 (MG iteration).  CPU TIME = 2.611002e+00
Vprtstp: iteration = 0
Vprtstp: relative residual = 1.000000e+00
Vprtstp: contraction number = 1.000000e+00
Vprtstp: iteration = 1
Vprtstp: relative residual = 6.439376e-02
Vprtstp: contraction number = 6.439376e-02
Vprtstp: iteration = 2
Vprtstp: relative residual = 8.079000e-03
Vprtstp: contraction number = 1.254625e-01
Vprtstp: iteration = 3
Vprtstp: relative residual = 1.198802e-03
Vprtstp: contraction number = 1.483849e-01
Vprtstp: iteration = 4
Vprtstp: relative residual = 2.003331e-04
Vprtstp: contraction number = 1.671112e-01
Vprtstp: iteration = 5
Vprtstp: relative residual = 3.696940e-05
Vprtstp: contraction number = 1.845396e-01
Vprtstp: iteration = 6
Vprtstp: relative residual = 7.822763e-06
Vprtstp: contraction number = 2.116010e-01
Vprtstp: iteration = 7
Vprtstp: relative residual = 1.950034e-06
Vprtstp: contraction number = 2.492769e-01
Vprtstp: iteration = 8
Vprtstp: relative residual = 5.515345e-07
Vprtstp: contraction number = 2.828332e-01
Vnm_tstop: stopping timer 30 (Vmgdrv2: solve).  CPU TIME = 4.214216e+00
Vnm_tstop: stopping timer 28 (Solver timer).  CPU TIME = 4.604426e+00
Vpmg_setPart:  lower corner = (-41.586, -32.2835, -51.8435)
Vpmg_setPart:  upper corner = (38.414, 47.7165, 28.1565)
Vpmg_setPart:  actual minima = (-41.586, -32.2835, -51.8435)
Vpmg_setPart:  actual maxima = (38.414, 47.7165, 28.1565)
Vpmg_setPart:  bflag[FRONT] = 0
Vpmg_setPart:  bflag[BACK] = 0
Vpmg_setPart:  bflag[LEFT] = 0
Vpmg_setPart:  bflag[RIGHT] = 0
Vpmg_setPart:  bflag[UP] = 0
Vpmg_setPart:  bflag[DOWN] = 0
Vnm_tstart: starting timer 29 (Energy timer)..
Vpmg_energy:  calculating only q-phi energy
Vpmg_qfEnergyVolume:  Calculating energy
Vpmg_energy:  qfEnergy = 1.577066075017E+05 kT
Vnm_tstop: stopping timer 29 (Energy timer).  CPU TIME = 1.603100e-02
Vnm_tstart: starting timer 30 (Force timer)..
Vnm_tstop: stopping timer 30 (Force timer).  CPU TIME = 1.000000e-06
Vnm_tstart: starting timer 27 (Setup timer)..
Setting up PBE object...
Vpbe_ctor2:  solute radius = 68.1141
Vpbe_ctor2:  solute dimensions = 110.419 x 85.574 x 104.449
Vpbe_ctor2:  solute charge = 1
Vpbe_ctor2:  bulk ionic strength = 0
Vpbe_ctor2:  xkappa = 0
Vpbe_ctor2:  Debye length = 0
Vpbe_ctor2:  zkappa2 = 0
Vpbe_ctor2:  zmagic = 7042.98
Vpbe_ctor2:  Constructing Vclist with 75 x 75 x 75 table
Vclist_ctor2:  Using 75 x 75 x 75 hash table
Vclist_ctor2:  automatic domain setup.
Vclist_ctor2:  Using 1.9 max radius
Vclist_setupGrid:  Grid lengths = (118.578, 94.435, 113.677)
Vclist_setupGrid:  Grid lower corner = (-60.875, -39.501, -68.682)
Vclist_assignAtoms:  Have 3533473 atom entries
Vacc_storeParms:  Surf. density = 10
Vacc_storeParms:  Max area = 191.134
Vacc_storeParms:  Using 1936-point reference sphere
Setting up PDE object...
Vpmp_ctor2:  Using meth = 2, mgsolv = 1
Setting PDE center to local center...
Vpmg_ctor2:  Filling boundary with old solution!
VPMG::focusFillBound -- New mesh mins = -21.586, -12.2835, -31.8435
VPMG::focusFillBound -- New mesh maxs = 18.414, 27.7165, 8.1565
VPMG::focusFillBound -- Old mesh mins = -41.586, -32.2835, -51.8435
VPMG::focusFillBound -- Old mesh maxs = 38.414, 47.7165, 28.1565
VPMG::extEnergy:  energy flag = 1
Vpmg_setPart:  lower corner = (-21.586, -12.2835, -31.8435)
Vpmg_setPart:  upper corner = (18.414, 27.7165, 8.1565)
Vpmg_setPart:  actual minima = (-41.586, -32.2835, -51.8435)
Vpmg_setPart:  actual maxima = (38.414, 47.7165, 28.1565)
Vpmg_setPart:  bflag[FRONT] = 0
Vpmg_setPart:  bflag[BACK] = 0
Vpmg_setPart:  bflag[LEFT] = 0
Vpmg_setPart:  bflag[RIGHT] = 0
Vpmg_setPart:  bflag[UP] = 0
Vpmg_setPart:  bflag[DOWN] = 0
VPMG::extEnergy:   Finding extEnergy dimensions...
VPMG::extEnergy    Disj part lower corner = (-21.586, -12.2835, -31.8435)
VPMG::extEnergy    Disj part upper corner = (18.414, 27.7165, 8.1565)
VPMG::extEnergy    Old lower corner = (-41.586, -32.2835, -51.8435)
VPMG::extEnergy    Old upper corner = (38.414, 47.7165, 28.1565)
Vpmg_qmEnergy:  Zero energy for zero ionic strength!
VPMG::extEnergy: extQmEnergy = 0 kT
Vpmg_qfEnergyVolume:  Calculating energy
VPMG::extEnergy: extQfEnergy = 119945 kT
VPMG::extEnergy: extDiEnergy = 60017.8 kT
Vpmg_fillco:  filling in source term.
fillcoCharge:  Calling fillcoChargeSpline2...
Vpmg_fillco:  filling in source term.
Vpmg_fillco:  marking ion and solvent accessibility.
fillcoCoef:  Calling fillcoCoefMol...
Vacc_SASA: Time elapsed: 1.229920
Vpmg_fillco:  done filling coefficient arrays
Vnm_tstop: stopping timer 27 (Setup timer).  CPU TIME = 2.313193e+00
Vnm_tstart: starting timer 28 (Solver timer)..
Vnm_tstart: starting timer 30 (Vmgdrv2: fine problem setup)..
Vbuildops: Fine: (097, 097, 097)
Vbuildops: Operator stencil (lev, numdia) = (1, 4)
Vnm_tstop: stopping timer 30 (Vmgdrv2: fine problem setup).  CPU TIME = 1.829400e-02
Vnm_tstart: starting timer 30 (Vmgdrv2: coarse problem setup)..
Vbuildops: Galer: (049, 049, 049)
Vbuildops: Galer: (025, 025, 025)
Vbuildops: Galer: (013, 013, 013)
Vnm_tstop: stopping timer 30 (Vmgdrv2: coarse problem setup).  CPU TIME = 3.589840e-01
Vnm_tstart: starting timer 30 (Vmgdrv2: solve)..
Vnm_tstop: stopping timer 40 (MG iteration).  CPU TIME = 9.571062e+00
Vprtstp: iteration = 0
Vprtstp: relative residual = 1.000000e+00
Vprtstp: contraction number = 1.000000e+00
Vprtstp: iteration = 1
Vprtstp: relative residual = 1.190347e-01
Vprtstp: contraction number = 1.190347e-01
Vprtstp: iteration = 2
Vprtstp: relative residual = 1.423203e-02
Vprtstp: contraction number = 1.195620e-01
Vprtstp: iteration = 3
Vprtstp: relative residual = 1.881003e-03
Vprtstp: contraction number = 1.321669e-01
Vprtstp: iteration = 4
Vprtstp: relative residual = 2.815815e-04
Vprtstp: contraction number = 1.496976e-01
Vprtstp: iteration = 5
Vprtstp: relative residual = 4.711963e-05
Vprtstp: contraction number = 1.673392e-01
Vprtstp: iteration = 6
Vprtstp: relative residual = 8.138950e-06
Vprtstp: contraction number = 1.727295e-01
Vprtstp: iteration = 7
Vprtstp: relative residual = 1.351401e-06
Vprtstp: contraction number = 1.660412e-01
Vprtstp: iteration = 8
Vprtstp: relative residual = 2.013897e-07
Vprtstp: contraction number = 1.490229e-01
Vnm_tstop: stopping timer 30 (Vmgdrv2: solve).  CPU TIME = 4.374460e+00
Vnm_tstop: stopping timer 28 (Solver timer).  CPU TIME = 4.758900e+00
Vpmg_setPart:  lower corner = (-21.586, -12.2835, -31.8435)
Vpmg_setPart:  upper corner = (18.414, 27.7165, 8.1565)
Vpmg_setPart:  actual minima = (-21.586, -12.2835, -31.8435)
Vpmg_setPart:  actual maxima = (18.414, 27.7165, 8.1565)
Vpmg_setPart:  bflag[FRONT] = 0
Vpmg_setPart:  bflag[BACK] = 0
Vpmg_setPart:  bflag[LEFT] = 0
Vpmg_setPart:  bflag[RIGHT] = 0
Vpmg_setPart:  bflag[UP] = 0
Vpmg_setPart:  bflag[DOWN] = 0
Vnm_tstart: starting timer 29 (Energy timer)..
Vpmg_energy:  calculating only q-phi energy
Vpmg_qfEnergyVolume:  Calculating energy
Vpmg_energy:  qfEnergy = 2.560457101536E+05 kT
Vnm_tstop: stopping timer 29 (Energy timer).  CPU TIME = 3.110000e-02
Vnm_tstart: starting timer 30 (Force timer)..
Vnm_tstop: stopping timer 30 (Force timer).  CPU TIME = 1.000000e-06
Vgrid_writeDX:  Opening virtual socket...
Vgrid_writeDX:  Writing to virtual socket...
Vgrid_writeDX:  Writing comments for ASC format.
Vnm_tstop: stopping timer 26 (APBS WALL CLOCK).  CPU TIME = 1.428473e+01
