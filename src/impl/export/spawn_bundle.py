from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ff14_the_hunt import HuntCrawlPacket, mark_to_display_dict
from ff14_the_hunt.locale.tag import HuntDisplayLocale
from ff14_the_hunt.models import HuntMarkRecord

from impl.export.map_mark import decode_region_map_bytes, mark_region_map_png


def spawn_bundle_dir(
    output_root: Path,
    *,
    mark: HuntMarkRecord,
    crawled_at: float,
) -> Path:
    """``年-月-日 / 世界 / 狩猎键-时分秒``。"""
    moment = datetime.fromtimestamp(crawled_at)
    date_part = moment.strftime("%Y-%m-%d")
    time_part = moment.strftime("%H%M%S")
    world_dir = mark.world_name.replace("/", "_").strip() or "unknown_world"
    hunt_part = mark.hunt_key.replace("/", "_").strip() or "unknown_hunt"
    return output_root / date_part / world_dir / f"{hunt_part}-{time_part}"


def write_spawn_bundle(
    output_root: Path,
    *,
    packet: HuntCrawlPacket,
    mark: HuntMarkRecord,
    locale: HuntDisplayLocale = HuntDisplayLocale.ZH,
) -> Path:
    """写入单次新检出聚合目录：JSON、原图、标点图。"""
    bundle_dir = spawn_bundle_dir(
        output_root,
        mark=mark,
        crawled_at=packet.crawled_at,
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)

    map_original: str | None = None
    map_marked: str | None = None
    png_bytes = decode_region_map_bytes(mark)
    if png_bytes is not None:
        original_path = bundle_dir / "map.png"
        original_path.write_bytes(png_bytes)
        map_original = original_path.name
        marked_path = bundle_dir / "map_marked.png"
        marked_path.write_bytes(mark_region_map_png(png_bytes, mark.spawn_points))
        map_marked = marked_path.name

    payload = {
        "爬取时间": packet.crawled_at,
        "狩猎": mark_to_display_dict(
            mark,
            locale=locale,
            embed_region_map_data=False,
            region_map_file_name=map_original,
        ),
        "文件": {
            "原图": map_original,
            "标点图": map_marked,
        },
    }
    manifest_path = bundle_dir / "spawn.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return bundle_dir
