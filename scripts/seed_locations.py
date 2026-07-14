import json
from pathlib import Path

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models.location import Location


RAW_DATA_DIR = Path("data/raw")

CHOSEONG = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ",
    "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ",
    "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]


def extract_initial_consonants(text: str) -> str:
    result: list[str] = []

    for char in text:
        code = ord(char)

        if 0xAC00 <= code <= 0xD7A3:
            index = (code - 0xAC00) // 588
            result.append(CHOSEONG[index])
        elif not char.isspace():
            result.append(char)

    return "".join(result)


def empty_to_none(value: object) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text if text else None


def to_float(value: object) -> float | None:
    text = empty_to_none(value)

    if text is None:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def seed_locations() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        json_files = sorted(RAW_DATA_DIR.glob("*.json"))

        if not json_files:
            print("data/raw 폴더에 JSON 파일이 없습니다.")
            return

        for json_file in json_files:
            with json_file.open("r", encoding="utf-8") as file:
                data = json.load(file)

            category = str(data.get("contentType", "")).strip()
            items = data.get("items", [])

            file_inserted = 0

            for item in items:
                source_id = str(item.get("contentid", "")).strip()

                if not source_id:
                    skipped += 1
                    continue

                exists = db.scalar(
                    select(Location.id).where(
                        Location.source_id == source_id
                    )
                )

                if exists is not None:
                    skipped += 1
                    continue

                name = str(item.get("title", "")).strip()

                if not name:
                    skipped += 1
                    continue

                location = Location(
                    source_id=source_id,
                    name=name,
                    initial_consonants=extract_initial_consonants(name),
                    category=category,
                    address=empty_to_none(item.get("addr1")),
                    longitude=to_float(item.get("mapx")),
                    latitude=to_float(item.get("mapy")),
                    image_url=empty_to_none(item.get("firstimage")),
                    thumbnail_url=empty_to_none(item.get("firstimage2")),
                )

                db.add(location)
                inserted += 1
                file_inserted += 1

            db.commit()
            print(f"{json_file.name}: {file_inserted}건 적재")

        print(f"전체 신규 적재: {inserted}건")
        print(f"중복 또는 제외: {skipped}건")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_locations()