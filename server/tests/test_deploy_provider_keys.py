import importlib.util
import io
import json
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import pytest


SCRIPT = pathlib.Path(__file__).parents[1] / "deploy" / "configure-hk-provider-keys.py"
SPEC = importlib.util.spec_from_file_location("configure_hk_provider_keys", SCRIPT)
configure = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(configure)


@pytest.fixture
def configured(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_PASSWORD=fixture\nOSS_BUCKET=private-bucket\n", encoding="utf-8")
    monkeypatch.setattr(configure, "ROOT", tmp_path)
    monkeypatch.setattr(configure, "ENV_FILE", env_file)
    monkeypatch.setattr(configure.sys, "stdin", io.StringIO())

    calls = []

    def run(command):
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(configure.subprocess, "run", run)
    for name in ("fchmod", "chown", "chmod"):
        monkeypatch.setattr(configure.os, name, lambda *args: None, raising=False)
    return env_file, calls


def test_rejects_partial_xfyun_without_changing_env(configured, monkeypatch):
    env_file, calls = configured
    baseline = env_file.read_bytes()
    monkeypatch.setattr(
        configure.sys,
        "stdin",
        io.StringIO('{"XFYUN_APP_ID":"fixture-app","XFYUN_API_KEY":"fixture-key"}'),
    )

    with pytest.raises(SystemExit, match="required together"):
        configure.main()

    assert env_file.read_bytes() == baseline
    assert calls == []


def test_writes_selected_deepseek_fields_without_echoing(configured, monkeypatch, capsys):
    env_file, calls = configured
    fake_key = "fixture-only-$with'quote"
    monkeypatch.setattr(
        configure.sys,
        "stdin",
        io.StringIO(
            '{"DEEPSEEK_API_KEY":"fixture-only-$with\'quote",'
            '"DEEPSEEK_MODEL":""}'
        ),
    )

    configure.main()

    output = capsys.readouterr().out
    stored = env_file.read_text(encoding="utf-8")
    assert "DB_PASSWORD=fixture" in stored
    assert "OSS_BUCKET=private-bucket" in stored
    assert "DEEPSEEK_MODEL=''" in stored
    assert fake_key not in output
    assert "Saved selected provider settings" in output
    assert "makes no vendor API request" in output
    assert len(calls) == 2
    assert calls[0][-1] == "api"
    assert "fixture-only" not in repr(calls)
    verification = calls[1][-1]
    assert "DEEPSEEK_MODEL" in verification
    assert "k in os.environ for k in selected" in verification
    assert "os.getenv(k) for k in required" in verification


def test_rejects_newlines_before_writing(configured, monkeypatch):
    env_file, calls = configured
    baseline = env_file.read_bytes()
    payload = '{"DEEPSEEK_API_KEY":"fixture-key","DEEPSEEK_MODEL":"bad\\nvalue"}'
    monkeypatch.setattr(configure.sys, "stdin", io.StringIO(payload))

    with pytest.raises(SystemExit, match="Newlines"):
        configure.main()

    assert env_file.read_bytes() == baseline
    assert calls == []


def test_rejects_unknown_environment_fields(configured, monkeypatch):
    env_file, calls = configured
    baseline = env_file.read_bytes()
    monkeypatch.setattr(
        configure.sys,
        "stdin",
        io.StringIO('{"AWS_SECRET_ACCESS_KEY":"fixture-secret"}'),
    )

    with pytest.raises(SystemExit, match="Invalid provider settings"):
        configure.main()

    assert env_file.read_bytes() == baseline
    assert calls == []


def test_writes_verified_ocr_price_without_provider_secret(configured, monkeypatch, capsys):
    env_file, calls = configured
    monkeypatch.setattr(
        configure.sys,
        "stdin",
        io.StringIO('{"XFYUN_OCR_UNIT_PRICE_RMB":"1.25"}'),
    )

    configure.main()

    assert "XFYUN_OCR_UNIT_PRICE_RMB='1.25'" in env_file.read_text(encoding="utf-8")
    assert "1.25" not in capsys.readouterr().out
    assert len(calls) == 2


def test_writes_zero_trial_ocr_price_without_provider_secret(configured, monkeypatch, capsys):
    env_file, calls = configured
    monkeypatch.setattr(
        configure.sys,
        "stdin",
        io.StringIO('{"XFYUN_OCR_UNIT_PRICE_RMB":"0.00"}'),
    )

    configure.main()

    assert "XFYUN_OCR_UNIT_PRICE_RMB='0.00'" in env_file.read_text(encoding="utf-8")
    assert "0.00" not in capsys.readouterr().out
    assert len(calls) == 2


@pytest.mark.parametrize("price", ["-1", "80.01", "NaN", "1.00001"])
def test_rejects_invalid_ocr_price_before_writing(configured, monkeypatch, price):
    env_file, calls = configured
    baseline = env_file.read_bytes()
    monkeypatch.setattr(
        configure.sys,
        "stdin",
        io.StringIO(json.dumps({"XFYUN_OCR_UNIT_PRICE_RMB": price})),
    )

    with pytest.raises(SystemExit):
        configure.main()

    assert env_file.read_bytes() == baseline
    assert calls == []


def test_env_quote_keeps_literal_dollars_and_backslashes():
    value = "fixture-$literal-\\slash-'quote"
    assert configure.env_quote(value) == "'fixture-$literal-\\slash-\\'quote'"
