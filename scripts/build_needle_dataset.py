"""Build Sugarcode's Needle fine-tuning set: python scripts/build_needle_dataset.py [out_dir] [per_tool]

Then fine-tune locally with cactus-compute/needle (https://github.com/cactus-compute/needle):
    needle finetune data/needle/sugarcode_tools.jsonl
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sugarcode.llm.dataset import build  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "needle"
per_tool = int(sys.argv[2]) if len(sys.argv) > 2 else 120
out.mkdir(parents=True, exist_ok=True)
rows, report = build(per_tool=per_tool)
with open(out / "sugarcode_tools.jsonl", "w") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
(out / "report.json").write_text(json.dumps(report, indent=1) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "skipped"}, indent=1))
