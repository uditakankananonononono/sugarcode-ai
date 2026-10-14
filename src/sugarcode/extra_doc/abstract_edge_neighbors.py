"""Row 1189: Contact Tracing.

PARTIAL: returns immediate neighbors of a supplied abstract vertex in an
undirected edge list. Duplicate and self edges are allowed. Module-local
caps of 30 edges and vertex labels 0-99 are not tracing standards.
No real-person identification, contact tracing or medical decisions.
"""
NOT_CLAIMED = ('real_person_identification', 'contact_tracing', 'medical_decisions')


def neighbors(edges, vertex):
    if type(edges) is not tuple or not 0 <= len(edges) <= 30:
        raise ValueError('edges: tuple of 0 to 30 pairs required')
    for i,edge in enumerate(edges):
        if type(edge) is not tuple or len(edge) != 2:
            raise ValueError(f'edges[{i}]: vertex pair required')
        for j,value in enumerate(edge):
            if type(value) is not int or not 0 <= value <= 99:
                raise ValueError(f'edges[{i}][{j}]: whole number 0 to 99 required')
    if type(vertex) is not int or not 0 <= vertex <= 99:
        raise ValueError('vertex: whole number 0 to 99 required')
    found = set()
    for a,b in edges:
        if a == vertex and b != vertex:
            found.add(b)
        if b == vertex and a != vertex:
            found.add(a)
    adjacent = tuple(sorted(found))
    return {'abstract_edge_neighbors_validated': False, 'not_claimed': NOT_CLAIMED,
            'neighbors': adjacent, 'degree': len(adjacent), 'isolated': len(adjacent) == 0}
