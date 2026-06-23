from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from procurement_pipeline.schemas.quote_input import QuoteComparisonInput


DEFAULT_SAMPLE_PATH = Path("data/sample_inputs/quote_comparison.json")


@dataclass(frozen=True, slots=True)
class QuoteInputLoadError(RuntimeError):
    path: Path
    reason: str

    def __str__(self) -> str:
        return f"{self.reason}: {self.path}"


def load_quote_comparison(path: Path) -> QuoteComparisonInput:
    try:
        json_text = path.read_text(encoding="utf-8")
        return QuoteComparisonInput.model_validate_json(json_text)
    except OSError as exc:
        raise QuoteInputLoadError(path=path, reason="Could not read quote input file") from exc
    except ValidationError as exc:
        raise QuoteInputLoadError(
            path=path,
            reason="Quote input JSON does not match the schema",
        ) from exc


def main() -> None:
    quote_input = load_quote_comparison(DEFAULT_SAMPLE_PATH)
    print(
        f"Loaded {quote_input.request_id} with "
        f"{len(quote_input.quotes)} supplier quotes."
    )


if __name__ == "__main__":
    main()
