from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from procurement_pipeline.schemas.historical_price import HistoricalUnitPriceInput


DEFAULT_HISTORICAL_UNIT_PRICE_PATH: Final = Path(
    "data/sample_inputs/historical_unit_prices.json"
)


@dataclass(frozen=True, slots=True)
class HistoricalUnitPriceLoadError(RuntimeError):
    path: Path
    reason: str

    def __str__(self) -> str:
        return f"{self.reason}: {self.path}"


def load_historical_unit_prices(path: Path) -> HistoricalUnitPriceInput:
    try:
        json_text = path.read_text(encoding="utf-8")
        return HistoricalUnitPriceInput.model_validate_json(json_text)
    except OSError as exc:
        raise HistoricalUnitPriceLoadError(
            path=path,
            reason="Could not read historical unit price file",
        ) from exc
    except ValidationError as exc:
        raise HistoricalUnitPriceLoadError(
            path=path,
            reason="Historical unit price JSON does not match the schema",
        ) from exc


def main() -> None:
    historical_prices = load_historical_unit_prices(DEFAULT_HISTORICAL_UNIT_PRICE_PATH)
    print(
        f"Loaded {len(historical_prices.purchase_records)} purchase records for "
        f"{historical_prices.item.name}."
    )


if __name__ == "__main__":
    main()
