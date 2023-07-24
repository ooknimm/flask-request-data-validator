import enum
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    Union,
)

from pydantic import TypeAdapter
from pydantic.fields import FieldInfo
from pydantic_core import ErrorDetails, PydanticUndefined, ValidationError

IncEx = Union[Set[int], Set[str], Dict[int, Any], Dict[str, Any]]


class FieldAdapter:
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
        self._field_info = FieldInfo(
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
        self.type_adapter: TypeAdapter[Any] = self.get_type_adapter()

    def get_type_adapter(self) -> TypeAdapter[Any]:
        return TypeAdapter(Annotated[self.field_info.annotation, self.field_info])  # type: ignore

    def validate(self, obj: Any, loc: Tuple[str, ...]) -> Tuple[Any, List[Dict[str, Any]]]:
        value, errors = None, []
        try:
            value = self.type_adapter.validate_python(obj)
        except ValidationError as exc:
            errors = self._regenerate_with_loc(exc.errors(), loc=loc)
        return value, errors

    def serialize(
        self,
        __instance: Any,
        *,
        mode: Literal["json", "python"] = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ):
        return self.type_adapter.dump_python(
            __instance,
            mode=mode,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )

    def _regenerate_with_loc(self, errors: List[ErrorDetails], loc: Tuple[str, ...]):
        return [{**error, "loc": loc + error["loc"]} for error in errors]

    @property
    def default(self) -> Any:
        return self.field_info.default

    @property
    def field_info(self):
        return self._field_info

    @field_info.setter
    def field_info(self, field_info: FieldInfo):
        self._field_info = field_info
        self.type_adapter = self.get_type_adapter()

    @property
    def alias(self) -> Optional[str]:
        return self.field_info.alias

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({(self.field_info.default)})"


class Param(FieldAdapter):
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


class Header(Param):
    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
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


class Path(Param):
    pass


class Query(Param):
    pass


class Cookie(Param):
    pass


class Body(FieldAdapter):
    def __init__(
        self,
        default: Any = PydanticUndefined,
        *,
        embed: bool = False,
        media_type: str = "application/json",
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
