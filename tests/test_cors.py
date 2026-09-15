from test_assessment_routes_auth import _boot_client


def test_cors_allows_trusted_origins(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_CORS_ORIGINS", "http://localhost:3000,https://sarvamai.github.io")

    with _boot_client(tmp_path, monkeypatch) as client:
        # Preflight from trusted origin
        r = client.options(
            "/health",
            headers={
                "Origin": "https://sarvamai.github.io",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.headers.get("access-control-allow-origin") == "https://sarvamai.github.io"

        # Preflight from allowed regex domain (Firebase / Render)
        r_fb = client.options(
            "/health",
            headers={
                "Origin": "https://academicos-staging.web.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r_fb.headers.get("access-control-allow-origin") == "https://academicos-staging.web.app"


def test_cors_blocks_untrusted_origins(tmp_path, monkeypatch):
    monkeypatch.setenv("ACOS_CORS_ORIGINS", "http://localhost:3000,https://sarvamai.github.io")

    with _boot_client(tmp_path, monkeypatch) as client:
        # Preflight from untrusted origin
        r = client.options(
            "/health",
            headers={
                "Origin": "https://malicious-attacker-site.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # Untrusted origin must NOT receive access-control-allow-origin
        assert "access-control-allow-origin" not in r.headers
