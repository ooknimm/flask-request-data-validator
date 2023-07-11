from typing import Any, Callable, Optional

from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


class Param(FieldInfo):
    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        **extra: Any,
    ) -> None:
        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            **extra,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{(self.default)}"


class Header(Param):
    pass


class Path(Param):
    pass


class Query(Param):
    pass


class Cookie(Param):
    pass


class Body(FieldInfo):
    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
        embed: bool = False,
        media_type: str = "application/json",
        alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: float | None = None,
        ge: float | None = None,
        lt: float | None = None,
        le: float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        **extra: Any,
    ) -> None:
        self.embed = embed
        self.media_type = media_type
        super().__init__(
            default=default,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            **extra,
        )


class Form(Body):
    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
        embed: bool = False,
        media_type: str = "application/x-www-form-urlencoded",
        alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: float | None = None,
        ge: float | None = None,
        lt: float | None = None,
        le: float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        **extra: Any,
    ) -> None:
        super().__init__(
            default,
            embed=embed,
            media_type=media_type,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            **extra,
        )


class File(Form):
    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
        embed: bool = False,
        media_type: str = "multipart/form-data",
        alias: str | None = None,
        title: str | None = None,
        description: str | None = None,
        gt: float | None = None,
        ge: float | None = None,
        lt: float | None = None,
        le: float | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        **extra: Any,
    ) -> None:
        super().__init__(
            default,
            embed=embed,
            media_type=media_type,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            **extra,
        )


class Depends:
    def __init__(self, dependency: Optional[Callable[..., Any]] = None) -> None:
        self.dependency = dependency

    def __repr__(self) -> str:
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        return f"{self.__class__.__name__}({attr})"
