"""Row 555 computer vision (PARTIAL): connected blobs in a small black-and-white image.

image is a list of 1 to 50 rows, each a list of the same length (1 to 50) of cells that are the whole numbers 0
(background) or 1 (foreground). connectivity is 4 (edge neighbours) or 8 (edges and corners). components(image,
connectivity=4) finds the groups of connected foreground cells and returns them in row-major order of their first
cell, each with its size and bounding box (min_row, min_col, max_row, max_col, inclusive). This is counting
connected pixels on a clean binary grid; it does not recognise objects, handle grey levels, noise or lighting."""
from collections import deque

MAX_SIDE = 50
STATUS_NOTE = ("PARTIAL: connected foreground cells on a supplied binary grid only; no object recognition, "
               "grey levels, noise handling or understanding of what the image shows")


def components(image, connectivity=4):
    if isinstance(connectivity, bool) or not isinstance(connectivity, int):
        raise ValueError("connectivity: integer required")
    if connectivity not in (4, 8):
        raise ValueError("connectivity: must be 4 or 8")
    if not isinstance(image, (list, tuple)):
        raise ValueError("image: list of rows required")
    if not 1 <= len(image) <= MAX_SIDE:
        raise ValueError(f"image: 1 to {MAX_SIDE} rows required")
    width = None
    grid = []
    for r, row in enumerate(image):
        if not isinstance(row, (list, tuple)):
            raise ValueError(f"image[{r}]: list required")
        if width is None:
            if not 1 <= len(row) <= MAX_SIDE:
                raise ValueError(f"image[{r}]: 1 to {MAX_SIDE} cells required")
            width = len(row)
        elif len(row) != width:
            raise ValueError(f"image[{r}]: {width} cells required")
        cells = []
        for c, v in enumerate(row):
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"image[{r}][{c}]: integer required")
            if v not in (0, 1):
                raise ValueError(f"image[{r}][{c}]: must be 0 or 1")
            cells.append(v)
        grid.append(cells)
    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        steps += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen = [[False] * width for _ in grid]
    found = []
    for r0 in range(len(grid)):
        for c0 in range(width):
            if grid[r0][c0] != 1 or seen[r0][c0]:
                continue
            seen[r0][c0] = True
            queue = deque([(r0, c0)])
            size = 0
            top, left, bottom, right = r0, c0, r0, c0
            while queue:
                r, c = queue.popleft()
                size += 1
                top, bottom = min(top, r), max(bottom, r)
                left, right = min(left, c), max(right, c)
                for dr, dc in steps:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < len(grid) and 0 <= nc < width and grid[nr][nc] == 1 and not seen[nr][nc]:
                        seen[nr][nc] = True
                        queue.append((nr, nc))
            found.append({"size": size, "bbox": (top, left, bottom, right)})
    return {"count": len(found), "components": found, "rows": len(grid), "cols": width,
            "status_note": STATUS_NOTE}
