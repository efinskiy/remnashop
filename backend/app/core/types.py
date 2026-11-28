from typing import TYPE_CHECKING, Annotated, NewType, TypeAlias
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, PlainValidator

if TYPE_CHECKING:
    ListStr: TypeAlias = list[str]
else:
    ListStr = NewType("ListStr", list[str])

StringList: TypeAlias = Annotated[
    ListStr, PlainValidator(lambda x: [s.strip() for s in x.split(",")])
]


def _known_zone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("must be an IANA time zone") from error
    return value


TimeZoneName: TypeAlias = Annotated[str, AfterValidator(_known_zone)]
