# Restriction enzyme table provenance

`enzymes.json`: recognition site (IUPAC), top-strand cut offset (`fst5`),
and bottom-strand cut offset (`fst3`) for 610 commercially available
restriction enzymes, extracted programmatically from Biopython 1.88's
`Bio.Restriction` module (`CommOnly` batch), which itself vendors the data
from REBASE (Roberts RJ, Vincze T, Posfai J, Macelis D. "REBASE - a
database for DNA restriction and modification." Nucleic Acids Res 2015,
43:D298-D299; current release at ftp.neb.com/rebase).

- Only single-recognition-site enzymes with fully defined cut positions are
  included. 13 CommOnly enzymes were excluded (two-site cutters such as
  BcgI/BsaXI, and enzymes with undefined cut data).
- Coordinate convention (identical to Biopython): `fst5` is the cut position
  on the 5'->3' strand relative to the first base of the recognition site;
  the bottom-strand cut is at `len(site) + fst3` in the same coordinates.
  `cut_bottom - cut_top > 0` means a 5' overhang, `< 0` a 3' overhang, `= 0`
  blunt. Offsets may lie outside the site (Type IIS downstream cutters).
- Regenerate: `python -c "from Bio.Restriction import CommOnly; ..."` as in
  the pb3 drop-76 STATUS.md entry; do not hand-edit.
