from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from random import choice, randint, uniform

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


def main() -> None:
    from shared.travelease_common import CATALOG_ITEMS

    target = ROOT / "data" / "samples" / "travelease_events.json"
    users = [f"user-{index:03d}" for index in range(1, 51)]
    rows = []
    for _ in range(400):
        item = choice(CATALOG_ITEMS)
        event_type = choice(["search", "booking", "review"])
        row = {
            "event_type": event_type,
            "user_id": choice(users),
            "item_id": item["item_id"],
            "city": item["city"],
            "service_type": item["service_type"],
            "amount": round(uniform(1200, item["base_price"]), 2),
            "score": randint(3, 5),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        rows.append(row)
    target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(rows)} rows to {target}")


if __name__ == "__main__":
    main()
