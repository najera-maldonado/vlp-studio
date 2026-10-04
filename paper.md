---
title: 'VLP Studio: a four-gate computational funnel for designing enzyme-loaded virus-like particle nanocapsules'
tags:
  - Python
  - structural biology
  - virus-like particles
  - enzyme encapsulation
  - protein engineering
  - molecular dynamics
  - drug delivery
authors:
  # TODO (author): confirm the exact spelling of your full legal name before submission,
  # and add your ORCID — JOSS requires at least one author with an ORCID.
  - name: Lucio Nájera Maldonado
    # orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  # TODO (author): replace with your institution, or keep "Independent researcher".
  - name: Independent researcher
    index: 1
date: 4 October 2026
bibliography: paper.bib
---

# Summary

Virus-like particles (VLPs) are self-assembling protein shells that can be loaded with a
cargo enzyme to act as nanoreactors: the shell protects the enzyme and shields it from the
immune system, while its pores let substrate in and product out [@patterson2012; @comellas2007].
Designing such a particle is not one question but several independent ones, each able to kill
a candidate on its own — and the expensive questions are not the ones that eliminate most
candidates.

**VLP Studio** organises that design problem as a **four-gate funnel**. Each gate asks one
physical question — does the substrate fit *through* the pore, does the enzyme fit *inside*
the shell, can the enzyme be de-immunised to survive *outside*, does the assembly *survive*
molecular dynamics — and a candidate must pass each gate before the next, more expensive one
is attempted. The platform pairs a web interface and 3D viewer with four independently
versioned engines that wrap established scientific software: HOLE [@smart1996] for pore
geometry, PyMOL [@pymol] for mutagenesis, RDKit [@rdkit] for substrate geometry, AutoDock
Vina [@trott2010] and Open Babel [@oboyle2011] for docking, Packmol [@martinez2009] for
packing, and AMBER [@case2005] with the SIRAH coarse-grained force field
[@darre2015; @machado2019] for dynamics.

The driving use case is enzyme replacement therapy for **Gaucher disease**, in which
glucocerebrosidase [@dvir2003] is deficient and its substrate glucosylceramide accumulates
[@grabowski2008]. That enzyme's structure ships with the repository as the worked example.

# Statement of need

Each step of VLP nanocapsule design already has good software, but the steps have no shared
workflow. A researcher asking whether a given enzyme can be usefully encapsulated in a given
capsid must currently run HOLE by hand on a pore structure, build mutants in PyMOL, compute a
substrate cross-section in RDKit, dock with Vina or a comparable engine, pack with Packmol,
and build a coarse-grained system for AMBER or GROMACS [@abraham2015] — each with its own
input conventions, each producing output the next step cannot read directly. The glue is
invariably ad-hoc scripting, which is where reproducibility is lost: the numbers survive, but
the parameters, versions and random seeds that produced them usually do not.

VLP Studio addresses three gaps.

**It composes the engines into one workflow with a common vocabulary.** The funnel is not a
presentational device but the ordering principle: the cheap, deterministic, geometric filters
come first, so a candidate whose substrate cannot physically traverse the pore is eliminated
before any GPU time is spent on dynamics. Gate 1 makes that comparison quantitative — the
minimum cross-sectional radius of the substrate, from its SMILES string, against the minimum
pore radius measured by HOLE on the structure's own principal symmetry axis. When the native
pore is too narrow, the same gate screens a mutant library for variants that widen it,
applying mutations symmetrically across all chains as the assembly's symmetry requires, then
docks the substrate into each variant to check that a wider pore still binds it.

**It makes the geometric results reproducible.** Packing is stochastic in Packmol, so a
single run is not an answer; VLP Studio runs a replicated experiment with a deterministic
seed base and reports the distribution rather than a best case. The Python environment is
pinned to exact versions, and the same lock file is used by the container image and by
continuous integration. A "golden" regression test freezes known numerical results of the
substrate cross-section calculation, so a change to the geometry code is caught even when
nothing crashes.

**It is explicit about what is measured and what is not.** Research software in this area
frequently presents placeholder output indistinguishably from computed output. Here, every
API response that is illustrative carries an `"illustrative": true` flag, real measurements
name the engine that produced them, and the interface and documentation label the
distinction. Engines that cannot legally be redistributed, such as HOLE and NetMHCIIpan
[@reynisson2020], are documented as user-supplied rather than quietly bundled.

# Software description

The platform is a monorepo of four independently versioned components.

**The Studio** (`nanocapsule-mvp`) is a Flask application with an NGL [@rose2015; @rose2018]
3D viewer, layered so that the HTTP routes contain no science: orchestration lives in one
service module per gate, with the domain logic below that. It exposes about thirty REST
endpoints, including a health endpoint reporting which engines and dependencies are actually
present, so a user always knows which gates will work in their installation.

**Poromania** is the gate 1 engine and the most mature part of the project: it identifies
pore-lining residues, generates mutants systematically, measures each with HOLE under
identical parameters, and docks a substrate into every variant to correlate pore radius with
binding affinity. It handles large flexible ligands; glucosylceramide has 125 atoms.

**PackMan** is the gate 4 engine: a complete coarse-grained MD protocol for the
enzyme-inside-capsid system, from packing through minimisation, staged heating, equilibration
and production, with a cpptraj analysis stage emitting the trajectory observables the Studio
is designed to display.

**sustratinaitor** builds the substrate in coarse-grained representation — glucosylceramide
had no SIRAH parameters, so it was mapped by hand to 17 beads and parametrised with GAFF2
[@wang2004] and AM1-BCC charges via antechamber [@wang2006] — and packs 200 copies of it
around the capsid as a starting configuration for dynamics.

# Current scope and limitations

Gates 1 and 2 are implemented end to end and produce real measurements. Gate 3 is a
placeholder: no epitope predictor is wired in, and its endpoint declares itself illustrative.
Gate 4 has a complete, runnable protocol, but **the molecular dynamics has not yet been
executed**, so no dynamics result in this repository should be treated as validated; the
corresponding interface tab shows synthetic curves, labelled as such. Three scientific
decisions are recorded as deliberately open rather than silently resolved: an internal-radius
safety margin, the coarse-grained versus all-atom resolution of the substrate system, and the
heating protocol. The Studio is a single-user local research server, without authentication or
a job queue. It is research software, not a clinical tool.

Running gate 4 and replacing gate 3's placeholder are the project's next steps. The software
is published now because the reproducible geometric filters, the engine wrappers and the
honest status reporting are useful on their own, and because publishing them makes the
dynamics work that follows auditable.

# Acknowledgements

VLP Studio coordinates established open scientific software rather than replacing it. The
author thanks the developers and maintainers of HOLE, PyMOL, Packmol, RDKit, Open Babel,
AutoDock Vina, AMBER, GROMACS, the SIRAH force field and NGL.

# References
