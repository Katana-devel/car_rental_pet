# currency_utils.py
import asyncio
from functools import wraps
from typing import Any, Sequence, Union, List, Tuple
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
import inspect

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.redis import get_redis, redis_manager
from src.repository.user import get_user_by_id
from src.services.auth import auth_service
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
        async def wrapper(
            *args,
            user_id: UUID = Depends(auth_service.get_current_user),
            db: AsyncSession = Depends(get_db),
            redis: Redis = Depends(get_redis),
            **kwargs
        ):
            sig = inspect.signature(func)
            try:
                bound = sig.bind_partial(*args, **kwargs)
                bound_args = bound.arguments
            except Exception:
                bound_args = {}


            effective_user_id = bound_args.get("user_id", user_id)
            effective_db = bound_args.get("db", db)
            effective_redis = bound_args.get("redis", redis)


            from fastapi.params import Depends as _FastAPIDependsClass

            def _is_dep_inst(x):
                return isinstance(x, _FastAPIDependsClass)

            if _is_dep_inst(effective_db) or _is_dep_inst(effective_user_id) or _is_dep_inst(effective_redis):

                raise RuntimeError(
                    "Decorated function called without resolved dependencies. "
                    "When calling this endpoint function from Python code (not via FastAPI), "
                    "pass the resolved dependencies explicitly as named args, e.g. "
                    "`await get_unconfirmed_booking(redis=redis, user_id=user_id)` "
                    "or call the original function without decorator via `func.__wrapped__`."
                )


            call_kwargs = dict(kwargs)
            bound_names = set(bound_args.keys())

            for name, value in (("user_id", effective_user_id), ("db", effective_db), ("redis", effective_redis)):
                if name in sig.parameters and name not in bound_names and name not in call_kwargs:
                    call_kwargs[name] = value

            result = await func(*args, **call_kwargs)

            if result is None:
                return result

            user = await get_user_by_id(effective_user_id, effective_db)
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

            coros = [convert(_to_float(value), currency, effective_redis) for (_, _, value) in work]

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

        return wrapper

    return decorator