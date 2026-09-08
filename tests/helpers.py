"""Shared test helpers."""

from afwip.core.cards import ENABLER_REGISTRY, SQUADRON_REGISTRY
from afwip.core.constants import Side


def draft_squadrons(side: Side, include=(), n: int = 4, camp=None,
                    exclude=(), flying_only=False) -> list[int]:
    """
    Build an exactly-n squadron draft for `side` (the squadron count is exact,
    like enablers): the given `include` ids first, padded with other legal ids.
    """
    chosen = list(include)
    for cid, profile in SQUADRON_REGISTRY.items():
        if len(chosen) >= n:
            break
        if profile.side != side or cid in chosen or cid in exclude:
            continue
        if camp is not None and not camp.squadron_allowed(cid):
            continue
        if flying_only and not profile.flying:
            continue
        chosen.append(cid)
    return chosen


def draft_enablers(side: Side, include=(), n: int = 6, camp=None, exclude=()) -> list[int]:
    """
    Build an exactly-n enabler draft for `side` (postures require the exact
    count): the given `include` ids first, padded with other legal card ids.
    """
    chosen = list(include)
    for cid, profile in ENABLER_REGISTRY.items():
        if len(chosen) >= n:
            break
        if profile.side != side or cid in chosen or cid in exclude:
            continue
        if camp is not None and not camp.enabler_allowed(cid):
            continue
        chosen.append(cid)
    return chosen
