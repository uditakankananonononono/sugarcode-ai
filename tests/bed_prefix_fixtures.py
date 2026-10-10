"""BED optional-prefix fixtures, no code execution on import."""
TOKENS = ("chr1", "0", "100", "demo", "50", "+", "0", "100", "255,0,0",
          "2", "10,5,", "0,15,")
ROWS_BY_WIDTH = {width: "\t".join(TOKENS[:width]) for width in range(3, 13)}
