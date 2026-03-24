# django-goldlapel

Django database backend for [Gold Lapel](https://goldlapel.com) — self-optimizing Postgres proxy that automatically creates materialized views and indexes. Includes L1 native cache — an in-process cache that serves repeated reads in microseconds with no TCP round-trip.

One-line change to your Django settings. Gold Lapel starts automatically on first database connection, with L1 cache enabled out of the box.

## Install

```bash
pip install django-goldlapel
```

## Usage

Replace your database engine:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_goldlapel",  # was: django.db.backends.postgresql
        "NAME": "mydb",
        "USER": "myuser",
        "PASSWORD": "mypassword",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

That's it. Gold Lapel starts when Django opens its first database connection, watches your query patterns, and automatically optimizes your database.

## Configuration

Optional proxy settings via `OPTIONS`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_goldlapel",
        "NAME": "mydb",
        "USER": "myuser",
        "PASSWORD": "mypassword",
        "HOST": "localhost",
        "PORT": "5432",
        "OPTIONS": {
            "goldlapel": {
                "config": {                              # proxy configuration
                    "mode": "butler",
                    "pool_size": 30,
                    "disable_n1": True,
                },
                "port": 9000,                            # proxy port (default: 7932)
                "extra_args": ["--threshold-duration-ms", "200"],
            }
        },
    }
}
```

The `config` dict maps directly to Gold Lapel's configuration options (snake_case keys). See the [Gold Lapel docs](https://goldlapel.com/docs) for available settings.

## Multiple Databases

If you have multiple `DATABASES` entries using this backend, each must use a different proxy port — otherwise the second database will route through the first's proxy:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_goldlapel",
        "HOST": "db1.example.com",
        # ...
        "OPTIONS": {"goldlapel": {"port": 7932}},
    },
    "analytics": {
        "ENGINE": "django_goldlapel",
        "HOST": "db2.example.com",
        # ...
        "OPTIONS": {"goldlapel": {"port": 7933}},
    },
}
```

## Requirements

- Python 3.9+
- Django 4.2+
- PostgreSQL (TCP connections only — Unix sockets are not supported)

## How It Works

This backend subclasses Django's built-in PostgreSQL backend. On first connection, it:

1. Builds the upstream PostgreSQL URL from your `DATABASES` settings
2. Starts the Gold Lapel proxy via [`goldlapel.start()`](https://github.com/goldlapel/goldlapel-python)
3. Returns a connection through the proxy (`127.0.0.1:7932`) with L1 native cache active

Everything else — migrations, ORM queries, raw SQL — works exactly as before, just faster. Repeated reads hit the L1 cache and return in microseconds without a TCP round-trip.
