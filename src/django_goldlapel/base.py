from urllib.parse import quote

import goldlapel
from django.db.backends.postgresql.base import DatabaseWrapper as PgDatabaseWrapper


def _build_upstream_url(settings):
    host = settings.get("HOST") or "localhost"
    port = str(settings.get("PORT") or 5432)

    if host.startswith("/"):
        raise ValueError(
            f"Gold Lapel cannot proxy Unix socket connections (HOST={host!r}). "
            "Use a TCP host instead."
        )

    user = settings.get("USER")
    password = settings.get("PASSWORD")

    if user:
        userinfo = quote(user, safe="")
        if password:
            userinfo += ":" + quote(password, safe="")
        userinfo += "@"
    else:
        userinfo = ""

    name = quote(settings.get("NAME") or "", safe="")

    return f"postgresql://{userinfo}{host}:{port}/{name}"


class DatabaseWrapper(PgDatabaseWrapper):
    def get_connection_params(self):
        params = super().get_connection_params()

        gl_opts = params.pop("goldlapel", {})
        gl_port = gl_opts.get("port", goldlapel.DEFAULT_PORT)
        gl_config = gl_opts.get("config")
        gl_extra_args = gl_opts.get("extra_args")

        upstream = _build_upstream_url(self.settings_dict)
        goldlapel.start(upstream, config=gl_config, port=gl_port, extra_args=gl_extra_args)

        params["host"] = "127.0.0.1"
        params["port"] = gl_port

        return params
