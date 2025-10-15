import asyncio
from functools import wraps
from typing import Any, Sequence, Union, List, Tuple
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
import inspect

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.redis import get_redis
from src.repository.user import get_user_by_id
from src.services.currency.currency_exchange import convert


def _is_mapping(obj: Any) -> bool:
    return isinstance(obj, dict)


def _get_all_by_path(obj: Any, path: str) -> List[Tuple[Any, str, Any]]:
    parts = path.split(".")
    if not parts:
        return []

    stack: List[Tuple[Any, List[str]]] = [(obj, parts)]
    results: List[Tuple[Any, str, Any]] = []

    while stack:
        cur, remaining = stack.pop()
        if cur is None:
            continue
        key = remaining[0]
        rest = remaining[1:]

        if isinstance(cur, list):
            for item in cur:
                stack.append((item, remaining))
            continue

        if _is_mapping(cur):
            nxt = cur.get(key)
        else:
            nxt = getattr(cur, key, None)

        if nxt is None:
            continue

        if rest:
            stack.append((nxt, rest))
        else:
            results.append((cur, key, nxt))

    return results


def _set_value_on_parent(parent: Any, key: str, value: Any) -> None:
    if _is_mapping(parent):
        parent[key] = value
        return

    try:
        setattr(parent, key, value)
        return
    except Exception:
        pass

    if hasattr(parent, "__dict__"):
        parent.__dict__[key] = value
        return


def with_currency(
    price_attrs: Union[str, Sequence[str]] = ("price",),
    *,
    all_matches: bool = False,
    replace_original: bool = True,
    converted_suffix: str = "_converted",
    parallel: bool = True,
    concurrency_limit: int = 50,
):
    if isinstance(price_attrs, str):
        attrs = [price_attrs]
    else:
        attrs = list(price_attrs)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id: UUID = kwargs.get("user_id")
            db: AsyncSession = kwargs.get("db")
            redis: Redis = kwargs.get("redis")

            if not any([user_id, db, redis]):
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        db = arg
                    elif isinstance(arg, Redis):
                        redis = arg
                    elif isinstance(arg, UUID):
                        user_id = arg

            if not all([user_id, db, redis]):
                raise RuntimeError(
                    f"Missing dependencies: user_id={user_id}, db={db}, redis={redis}. "
                    "Ensure FastAPI provides them via Depends in the route."
                )

            result = await func(*args, **kwargs)
            if result is None:
                return result

            user = await get_user_by_id(user_id, db)
            currency = (user.currency or "usd").lower()

            items = result if isinstance(result, list) else [result]
            work: List[Tuple[Any, str, Any]] = []

            for item in items:
                for attr in attrs:
                    matches = _get_all_by_path(item, attr)
                    if not matches:
                        continue
                    for parent, key, val in matches:
                        work.append((parent, key, val))
                    if not all_matches:
                        break

            if not work:
                return result

            def _to_float(v: Any) -> float:
                if isinstance(v, Decimal):
                    return float(v)
                try:
                    return float(v)
                except Exception:
                    return 0.0

            coros = [convert(_to_float(value), currency, redis) for (_, _, value) in work]

            if parallel and coros:
                sem = asyncio.Semaphore(concurrency_limit)

                async def _sem_coro(c):
                    async with sem:
                        return await c

                converted_list = await asyncio.gather(*[_sem_coro(c) for c in coros])
            elif parallel:
                converted_list = await asyncio.gather(*coros) if coros else []
            else:
                converted_list = [await c for c in coros]

            for (parent, key, _old), conv in zip(work, converted_list):
                new_value = conv.get("price")
                new_currency = conv.get("currency", currency)

                if replace_original:
                    _set_value_on_parent(parent, key, new_value)
                else:
                    _set_value_on_parent(parent, f"{key}{converted_suffix}", new_value)

                _set_value_on_parent(parent, "currency", new_currency)

            return result
        wrapper.__signature__ = inspect.signature(func)
        return wrapper

    return decorator