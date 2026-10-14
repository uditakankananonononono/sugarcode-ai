import cmath
import math
import random
import pytest
from sugarcode.extra_doc import architectural_rendering as a

P = a.project
A = pytest.approx


def test_constants():
    assert a.MAX_POINTS == 1000 and a.STATUS_NOTE.startswith("PARTIAL")
    assert "no lighting" in a.STATUS_NOTE


def test_hand_projection():
    assert P([(1, 2, 4)], focal_px=100) == [(25.0, 50.0)]
    assert P([(1, 2, 4)]) == [(250.0, 500.0)]  # default focal 1000
    assert P([(10, 5, 2)], cam_pos=(10, 5, 0), focal_px=100) == [(0.0, 0.0)]
    assert P([(12, 5, 4)], cam_pos=(10, 5, 0), focal_px=100) == [(50.0, 0.0)]
    assert P([(-3, -6, 3)], focal_px=10) == [(-10.0, -20.0)]
    assert P([(0, 0, 1), (0, 0, 2)], focal_px=7) == [(0.0, 0.0), (0.0, 0.0)]


def test_yaw_quarter_turn_hand():
    # facing +x: right-hand side is -z; point 4 ahead, 1 to the right (z = -1), 2 up
    (u, v), = P([(4, 2, -1)], yaw_deg=90, focal_px=100)
    assert u == A(25.0, abs=1e-9) and v == A(50.0, abs=1e-9)
    (u, v), = P([(4, 2, 1)], yaw_deg=90, focal_px=100)
    assert u == A(-25.0, abs=1e-9)
    (u, v), = P([(1, 0, 1)], yaw_deg=45, focal_px=100)  # straight ahead on the 45 degree diagonal
    assert u == A(0.0, abs=1e-9) and v == 0.0
    (u, v), = P([(0, 0, 1)], yaw_deg=-45, focal_px=100)  # camera turned toward -x: the point is to its right
    assert u == A(100.0, abs=1e-9) and v == 0.0


def test_negative_zero_is_normalised():
    u, v = P([(-0.0, -0.0, 5)])[0]
    assert math.copysign(1, u) == 1 and math.copysign(1, v) == 1
    u, v = P([(0, 0, 5)], cam_pos=(0.0, 0.0, 0.0))[0]
    assert math.copysign(1, u) == 1 and math.copysign(1, v) == 1


def test_behind_or_on_camera_plane_rejected():
    for pt in [(0, 0, 0), (0, 0, -1), (5, 5, -0.001)]:
        with pytest.raises(ValueError, match="point is behind the camera"):
            P([pt])
    with pytest.raises(ValueError, match="point is behind the camera"):
        P([(1, 0, 0)], yaw_deg=0)
    with pytest.raises(ValueError, match="point is behind the camera"):
        P([(0, 0, 5)], yaw_deg=180)
    assert P([(0, 0, 0.001)], focal_px=1)[0] == (0.0, 0.0)


def test_random_against_complex_rotation_oracle():
    rnd = random.Random(31)
    for _ in range(200):
        cam = tuple(rnd.uniform(-50, 50) for _ in range(3))
        yaw = rnd.uniform(-180, 180)
        f = rnd.uniform(1, 2000)
        pt = tuple(rnd.uniform(-100, 100) for _ in range(3))
        q = complex(pt[2] - cam[2], pt[0] - cam[0]) * cmath.exp(-1j * math.radians(yaw))
        if q.real <= 1e-6:
            with pytest.raises(ValueError):
                P([pt], cam, yaw, f)
            continue
        u, v = P([pt], cam, yaw, f)[0]
        assert u == A(f * q.imag / q.real, rel=1e-9, abs=1e-9)
        assert v == A(f * (pt[1] - cam[1]) / q.real, rel=1e-9, abs=1e-9)


def test_box_wireframe_hand():
    r = a.box_wireframe((-1, 0, 4), (2, 3, 2), focal_px=100)
    assert r["bounds"] == (A(-25.0), A(0.0), A(25.0), A(75.0))
    e = r["edges"]
    assert len(e) == 12 and r["status"] == a.STATUS_NOTE
    assert e[0] == ((A(-25.0), A(0.0)), (A(25.0), A(0.0)))            # bottom near edge along x
    assert e[1] == ((A(25.0), A(0.0)), (A(25.0), A(75.0)))            # right near edge going up
    assert e[8] == ((A(-25.0), A(0.0)), (A(-100 / 6), A(0.0)))        # depth edge, x = -1, z 4 to 6
    assert e[11] == ((A(25.0), A(75.0)), (A(100 / 6), A(50.0)))       # top right depth edge
    from collections import Counter
    pts = Counter(p for ed in e for p in ed)
    assert len(pts) == 8 and set(pts.values()) == {3}


def test_box_wireframe_camera_offset_and_default_focal():
    r = a.box_wireframe((0, 0, 10), (1, 1, 1), cam_pos=(0.5, 0.5, 0), focal_px=1000)
    b = r["bounds"]
    assert b[0] == A(-50.0) and b[2] == A(50.0) and b[1] == A(-50.0) and b[3] == A(50.0)
    assert a.box_wireframe((0, 0, 1), (1, 1, 1))["bounds"][2] == A(1000.0)


def test_shadow_hand_and_oracle():
    assert a.shadow_length(10, 45) == A(10.0, abs=1e-9)
    assert a.shadow_length(10, 30) == A(10 * math.sqrt(3), rel=1e-12)
    assert a.shadow_length(10, 90) == A(0.0, abs=1e-9)
    assert a.shadow_length(0, 45) == 0.0
    assert a.shadow_length(3, 60) == A(3 / math.sqrt(3), rel=1e-12)
    rnd = random.Random(2)
    for _ in range(50):
        h, alt = rnd.uniform(0, 100), rnd.uniform(1, 90)
        assert a.shadow_length(h, alt) == A(h * math.cos(math.radians(alt)) / math.sin(math.radians(alt)), rel=1e-9, abs=1e-12)
    assert a.shadow_length(100000, 1) == A(100000 / math.tan(math.radians(1)), rel=1e-12)


@pytest.mark.parametrize("call", [
    lambda: P([]), lambda: P([(0, 0, 1)] * 1001), lambda: P("ab"), lambda: P(None), lambda: P([5]),
    lambda: P([(1, 2)]), lambda: P([(1, 2, 3, 4)]), lambda: P([(True, 0, 1)]), lambda: P([(0, 0, "1")]),
    lambda: P([(100001, 0, 1)]), lambda: P([(0, -100001, 1)]), lambda: P([(0, 0, float("nan"))]),
    lambda: P([(0, 0, 1)], cam_pos=(0, 0)), lambda: P([(0, 0, 1)], cam_pos="abc"), lambda: P([(0, 0, 1)], cam_pos=(0, 0, 100001)),
    lambda: P([(0, 0, 1)], cam_pos=(True, 0, 0)), lambda: P([(0, 0, 1)], yaw_deg=181), lambda: P([(0, 0, 1)], yaw_deg=-181),
    lambda: P([(0, 0, 1)], yaw_deg=True), lambda: P([(0, 0, 1)], focal_px=0.5), lambda: P([(0, 0, 1)], focal_px=100001),
    lambda: P([(0, 0, 1)], focal_px="1"), lambda: P([(0, 0, 1)], yaw_deg=float("inf")),
    lambda: a.shadow_length(-1, 45), lambda: a.shadow_length(100001, 45), lambda: a.shadow_length(1, 0.9),
    lambda: a.shadow_length(1, 90.1), lambda: a.shadow_length(True, 45), lambda: a.shadow_length(1, "45"),
    lambda: a.shadow_length(1, float("nan")), lambda: a.shadow_length(2e9, 45),
    lambda: a.box_wireframe((0, 0, 1), (0, 1, 1)), lambda: a.box_wireframe((0, 0, 1), (1, 1, 100001)),
    lambda: a.box_wireframe((0, 0, 100001), (1, 1, 1)), lambda: a.box_wireframe((0, 0, -5), (1, 1, 1)),
    lambda: a.box_wireframe((True, 0, 1), (1, 1, 1)),
])
def test_rejects(call):
    with pytest.raises(ValueError):
        call()


def test_limits_and_messages():
    assert len(P([(0, 0, 1)] * 1000)) == 1000
    assert P([(0, 0, 100000)], cam_pos=(0, 0, 100000 - 1), focal_px=100000)[0] == (0.0, 0.0)
    assert P([(0, 0, 1)], yaw_deg=180 - 180)[0] == (0.0, 0.0)
    assert P([(0, 0, 1)], focal_px=1)[0] == (0.0, 0.0) and P([(0, 0, 1)], focal_px=100000)[0] == (0.0, 0.0)
    with pytest.raises(ValueError, match="points: 1 to 1000 required"):
        P([])
    with pytest.raises(ValueError, match=r"cam_pos: \(x, y, z\) required"):
        P([(0, 0, 1)], cam_pos=(1, 2))
    with pytest.raises(ValueError, match=r"point: \(x, y, z\) required"):
        P([(1, 2)])
    with pytest.raises(ValueError, match="yaw_deg: must be within"):
        P([(0, 0, 1)], yaw_deg=181)
    with pytest.raises(ValueError, match="focal_px: must be within"):
        P([(0, 0, 1)], focal_px=0)
    with pytest.raises(ValueError, match="size: must be within"):
        a.box_wireframe((0, 0, 1), (0, 1, 1))
    with pytest.raises(ValueError, match="origin: must be within"):
        a.box_wireframe((0, 0, 100001), (1, 1, 1))
    with pytest.raises(ValueError, match="sun_altitude_deg: must be within"):
        a.shadow_length(1, 0.5)
    with pytest.raises(ValueError, match="height: must be within"):
        a.shadow_length(-0.1, 45)
    with pytest.raises(ValueError, match="point: magnitude above 1e9"):
        P([(2e9, 0, 1)])
    with pytest.raises(ValueError, match="point: must be within"):
        P([(1e9, 0, 1)])
    with pytest.raises(ValueError, match="point: must be within"):
        P([(999999999, 0, 1)])
    with pytest.raises(ValueError, match="point: magnitude above 1e9"):
        P([(1000000001.0, 0, 1)])
    with pytest.raises(ValueError, match="point: number required"):
        P([(True, 0, 1)])
    with pytest.raises(ValueError, match="point: finite"):
        P([(float("nan"), 0, 1)])
    assert a.box_wireframe((0, 0, 1), (0.001, 0.001, 0.001))["bounds"] is not None
    assert a.shadow_length(0, 1) == 0.0 and a.shadow_length(1, 90) < 1e-9


def test_range_edges_on_both_sides():
    assert P([(0, 0, 1)], cam_pos=(-100000, 100000, -100000))[0][0] == A(1000 * 100000 / 100001)
    assert P([(0, 0, 1)], cam_pos=(100000, -100000, -100000))[0][0] == A(-1000 * 100000 / 100001)
    for bad in [(-100001, 0, 0), (100001, 0, 0), (0, -100001, 0), (0, 100001, 0), (0, 0, -100001), (0, 0, 100001)]:
        with pytest.raises(ValueError, match="cam_pos: must be within"):
            P([(0, 0, 1)], cam_pos=bad)
    assert P([(0, 0, -5)], yaw_deg=-180)[0] == (A(0.0, abs=1e-9), 0.0) and P([(0, 0, -5)], yaw_deg=180)[0] == (A(0.0, abs=1e-9), 0.0)
    with pytest.raises(ValueError, match="yaw_deg: must be within"):
        P([(0, 0, 1)], yaw_deg=-180.5)
    assert a.box_wireframe((-100000, -100000, 5), (1, 1, 1))["bounds"] is not None
    for bad in [(-100001, 0, 1), (100001, 0, 1), (0, -100001, 1), (0, 100001, 1), (0, 0, 100001)]:
        with pytest.raises(ValueError, match="origin: must be within"):
            a.box_wireframe(bad, (1, 1, 1))
    for bad in [(100001, 1, 1), (1, 100001, 1), (1, 1, 100001), (0.0009, 1, 1)]:
        with pytest.raises(ValueError, match="size: must be within"):
            a.box_wireframe((0, 0, 1), bad)


def test_size_upper_edge_accepted():
    assert a.box_wireframe((0, 0, 1), (100000, 100000, 99999))["bounds"] is not None


def test_minimum_depth_refusal_and_boundary():
    assert a.MIN_DEPTH == 1e-6
    for z in (5e-324, 1e-300, 1e-9, 9.9e-7):
        with pytest.raises(ValueError, match="point is closer than 1e-06 to the camera plane"):
            P([(1, 1, z)])
    assert P([(1, 1, 1e-6)], focal_px=1) == [(1000000.0, 1000000.0)]
    assert P([(1, 1, 1.1e-6)], focal_px=1)[0][0] == A(1 / 1.1e-6, rel=1e-12)
    with pytest.raises(ValueError, match="point is behind the camera"):
        P([(1, 1, 0.0)])
    with pytest.raises(ValueError, match="point is behind the camera"):
        P([(1, 1, -5e-324)])
    # every accepted output is finite, including the extreme corner
    u, v = P([(100000, -100000, 1e-6)], focal_px=100000)[0]
    assert math.isfinite(u) and math.isfinite(v)


def test_origin_lower_bound_valid():
    r = a.box_wireframe((-100000, 0, 1), (0.001, 0.001, 0.001))
    assert len(r["edges"]) == 12
    r = a.box_wireframe((0, -100000, 1), (0.001, 0.001, 0.001))
    assert len(r["edges"]) == 12


def test_origin_upper_bound_valid_just_below_cap():
    r = a.box_wireframe((99999.5, 0, 1), (0.001, 0.001, 0.001))
    assert len(r["edges"]) == 12
    r = a.box_wireframe((0, 99999.5, 1), (0.001, 0.001, 0.001))
    assert len(r["edges"]) == 12
    r = a.box_wireframe((0, 0, 99999.5), (0.001, 0.001, 0.001))
    assert len(r["edges"]) == 12
