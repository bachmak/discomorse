def resolve[T](catalog: dict[str, T], name: str, kind: str) -> T:
    """Pick the type a name stands for."""
    try:
        return catalog[name]
    except KeyError as exc:
        known = ", ".join(sorted(catalog)) or "none"
        raise KeyError(f"Unknown {kind}: {name!r} (known: {known})") from exc
