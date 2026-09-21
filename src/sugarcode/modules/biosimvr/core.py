from __future__ import annotations
import math


class LabScene:
    """A 3D lab: benches, instruments, positions - the 'VR' world model."""

    def __init__(self):
        self.objects: dict[str, dict] = {}
        self.log: list[dict] = []

    def add(self, name: str, kind: str, pos: tuple[float, float, float],
            state: dict | None = None) -> dict:
        self.objects[name] = {"kind": kind, "pos": tuple(pos), "state": state or {}}
        return self.objects[name]

    def move_to(self, obj: str, target: str) -> float:
        a, b = self.objects[obj], self.objects[target]
        d = math.dist(a["pos"], b["pos"])
        a["pos"] = b["pos"]
        self.log.append({"action": "move", "obj": obj, "to": target, "distance_m": round(d, 2)})
        return d

    def interact(self, obj: str, command: str, **kwargs) -> dict:
        o = self.objects[obj]
        handler = getattr(self, f"_cmd_{command}", None)
        if handler is None:
            raise ValueError(f"instrument {obj} has no command {command!r}")
        result = handler(o, **kwargs)
        self.log.append({"action": command, "obj": obj, "result": result})
        return result

    def _cmd_pipette(self, o, volume_uL: float = 10.0):
        if volume_uL <= 0 or volume_uL > 1000:
            raise ValueError("pipette range 0-1000 uL")
        o["state"]["last_volume_uL"] = volume_uL
        return {"dispensed_uL": volume_uL, "tip": "fresh"}

    def _cmd_incubate(self, o, minutes: float = 30, temp_C: float = 37.0):
        o["state"]["elapsed_min"] = o["state"].get("elapsed_min", 0) + minutes
        return {"temp_C": temp_C, "total_min": o["state"]["elapsed_min"]}

    def _cmd_measure(self, o, assay: str = "fluorescence"):
        val = o["state"].get("signal", 0.0)
        return {"assay": assay, "reading": round(val, 3)}


def default_lab() -> LabScene:
    lab = LabScene()
    lab.add("bench_1", "bench", (0, 0, 0))
    lab.add("p1000", "pipette", (0.5, 0, 0.2))
    lab.add("plate_96", "plate", (1.0, 0, 0), state={"signal": 0.0})
    lab.add("incubator", "incubator", (3, 0, 0))
    lab.add("reader", "plate_reader", (4, 1, 0))
    return lab


def run_session(task: str = "crispr_transfection") -> dict:
    """Scripted experiment in the virtual lab; returns observations + conclusions."""
    lab = default_lab()
    observations = []
    if task == "crispr_transfection":
        lab.move_to("p1000", "plate_96")
        r1 = lab.interact("p1000", "pipette", volume_uL=50)
        observations.append(f"dispensed {r1['dispensed_uL']} uL Cas9-RNP transfection mix")
        lab.move_to("plate_96", "incubator")
        r2 = lab.interact("incubator", "incubate", minutes=2880, temp_C=37.0)
        observations.append(f"incubated 48 h at {r2['temp_C']} C")
        lab.objects["plate_96"]["state"]["signal"] = 0.72
        lab.move_to("plate_96", "reader")
        r3 = lab.interact("reader", "measure", assay="fluorescence")
        observations.append(f"reporter fluorescence {r3['reading']} (edit proxy)")
        conclusion = ("editing reporter positive at 0.72 RFU - transfection succeeded; "
                      "confirm indels by NGS before claiming edit rate")
    elif task == "molecular_docking":
        from ..docking_studio.core import dock
        lab.interact("p1000", "pipette", volume_uL=10)
        res = dock("CCO", "kinase_pocket", seed=1)
        observations.append(f"dock score {res.get('score', res)}")
        conclusion = "binding pose scored in silico; wet-lab confirmation via SPR next"
    else:
        raise KeyError(f"unknown task {task!r}; have crispr_transfection, molecular_docking")
    return {
        "task": task, "scene": {k: v["pos"] for k, v in lab.objects.items()},
        "observations": observations, "conclusion": conclusion,
        "action_log": lab.log,
        "cost_note": "virtual run: zero consumables, full protocol replayability",
    }
