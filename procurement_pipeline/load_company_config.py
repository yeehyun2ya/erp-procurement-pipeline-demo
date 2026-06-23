from dataclasses import dataclass
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from procurement_pipeline.schemas.company_config import CompanyConfig


DEFAULT_COMPANY_CONFIG_PATH: Final = Path("configs/companies/company_demo.json")


@dataclass(frozen=True, slots=True)
class CompanyConfigLoadError(RuntimeError):
    path: Path
    reason: str

    def __str__(self) -> str:
        return f"{self.reason}: {self.path}"


def load_company_config(path: Path) -> CompanyConfig:
    try:
        json_text = path.read_text(encoding="utf-8")
        return CompanyConfig.model_validate_json(json_text)
    except OSError as exc:
        raise CompanyConfigLoadError(
            path=path,
            reason="Could not read company config file",
        ) from exc
    except ValidationError as exc:
        raise CompanyConfigLoadError(
            path=path,
            reason="Company config JSON does not match the schema",
        ) from exc


def main() -> None:
    company_config = load_company_config(DEFAULT_COMPANY_CONFIG_PATH)
    print(
        f"Loaded {company_config.company_id} config with "
        f"{len(company_config.approval_route_policy.route_hints)} route hints."
    )


if __name__ == "__main__":
    main()
