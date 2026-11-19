"""Tests for the typed config module."""

import json

import pytest

from convopus.config import Config, config_path, load, print_config, write_default


def test_load_creates_missing_file_with_defaults(isolated_config):
    assert not isolated_config.is_file()
    config = load()
    assert isolated_config.is_file()
    assert config == Config()


def test_written_default_round_trips(isolated_config):
    write_default()
    on_disk = json.loads(isolated_config.read_text(encoding="utf-8"))
    assert on_disk["bitrate"] == "128k"
    assert on_disk["container"] == ".opus"
    assert isinstance(on_disk["common_types"], list)


def test_load_reads_existing_values(isolated_config):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(
        json.dumps(
            {
                "bitrate": "96k",
                "container": ".ogg",
                "keep": False,
                "vbr": "off",
                "recursive": True,
            }
        ),
        encoding="utf-8",
    )
    config = load()
    assert config.bitrate == "96k"
    assert config.container == ".ogg"
    assert config.keep is False
    assert config.vbr == "off"
    assert config.recursive is True


def test_load_accepts_legacy_uppercase_keys(isolated_config):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(
        json.dumps({"BITRATE": "160k", "CONTAINER": ".oga", "RECURSIVE": True}),
        encoding="utf-8",
    )
    config = load()
    assert config.bitrate == "160k"
    assert config.container == ".oga"
    assert config.recursive is True
    assert config.common_types == Config().common_types


def test_load_fills_missing_keys_from_defaults(isolated_config, capsys):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(json.dumps({"bitrate": "96k"}), encoding="utf-8")
    config = load()
    assert config.bitrate == "96k"
    assert config.container == Config().container
    assert config.keep is True
    assert capsys.readouterr().err == ""


def test_load_repairs_invalid_values_with_warning(isolated_config, capsys):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(
        json.dumps({"vbr": "maybe", "keep": "sometimes", "bitrate": ""}),
        encoding="utf-8",
    )
    config = load()
    stderr = capsys.readouterr().err
    assert config.vbr == "on"
    assert config.keep is True
    assert config.bitrate == "128k"
    assert "vbr" in stderr
    assert "keep" in stderr


def test_load_normalizes_extensions(isolated_config):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(
        json.dumps({"container": "opus", "COMMONTYPES": ["FLAC", "wav", ".Aac"]}),
        encoding="utf-8",
    )
    config = load()
    assert config.container == ".opus"
    assert config.common_types == (".flac", ".wav", ".aac")


def test_load_corrupt_json_falls_back_to_defaults(isolated_config, capsys):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text("{not json", encoding="utf-8")
    assert load() == Config()
    assert "could not read" in capsys.readouterr().err


def test_load_non_object_root_falls_back_to_defaults(isolated_config, capsys):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text("[1, 2, 3]", encoding="utf-8")
    assert load() == Config()
    assert "JSON object" in capsys.readouterr().err


def test_config_path_env_override(monkeypatch, tmp_path):
    override = tmp_path / "portable" / "convopus.json"
    monkeypatch.setenv("CONVOPUS_CONFIG", str(override))
    assert config_path() == override


def test_load_explicit_path_does_not_touch_default(isolated_config, tmp_path):
    explicit = tmp_path / "other.json"
    config = load(explicit)
    assert config == Config()
    assert explicit.is_file()
    assert not isolated_config.exists()


def test_load_migrates_legacy_config(monkeypatch, isolated_config, tmp_path, capsys):
    """A config left by pre-platformdirs builds (roaming dir) is migrated."""
    legacy_dir = tmp_path / "legacy-roaming"
    new_dir = tmp_path / "new-local"

    def fake_user_config_path(*args, **kwargs):
        return legacy_dir if kwargs.get("roaming") else new_dir

    monkeypatch.setattr("convopus.config.user_config_path", fake_user_config_path)
    monkeypatch.delenv("CONVOPUS_CONFIG")
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "config.json").write_text(
        json.dumps({"BITRATE": "160k", "CONTAINER": ".ogg"}), encoding="utf-8"
    )

    config = load()

    assert config.bitrate == "160k"
    assert config.container == ".ogg"
    assert (new_dir / "config.json").is_file()
    assert "migrating" in capsys.readouterr().err


def test_migration_skipped_when_env_override_set(
    monkeypatch, isolated_config, tmp_path
):
    def fake_user_config_path(*args, **kwargs):
        return tmp_path / "legacy" if kwargs.get("roaming") else tmp_path / "ignored"

    monkeypatch.setattr("convopus.config.user_config_path", fake_user_config_path)
    legacy = tmp_path / "legacy" / "config.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({"bitrate": "320k"}), encoding="utf-8")

    config = load()

    assert config == Config()
    assert isolated_config.is_file()
    assert not (tmp_path / "ignored" / "config.json").exists()


def test_from_mapping_ignores_unknown_keys():
    config = Config.from_mapping({"future_option": 42, "bitrate": "64k"})
    assert config.bitrate == "64k"
    assert config == Config(bitrate="64k")


def test_from_mapping_warns_on_bad_common_types(capsys):
    config = Config.from_mapping({"COMMONTYPES": "flac"})
    assert config.common_types == Config().common_types
    assert "common_types" in capsys.readouterr().err


def test_from_mapping_coerces_boolean_forms():
    assert Config.from_mapping({"keep": 0}).keep is False
    assert Config.from_mapping({"keep": 1}).keep is True
    assert Config.from_mapping({"keep": "yes"}).keep is True
    assert Config.from_mapping({"multi_threading": "off"}).multi_threading is False
    assert Config.from_mapping({"recursive": "ON"}).recursive is True


def test_from_mapping_reads_existing_file_policy():
    assert Config.from_mapping({"OVERWRITE": True}).overwrite is True
    assert Config.from_mapping({"skip_existing": "yes"}).skip_existing is True


def test_both_existing_policies_collapse_to_overwrite(capsys):
    config = Config.from_mapping({"overwrite": True, "skip_existing": True})
    assert config.overwrite is True
    assert config.skip_existing is False
    assert "skipping is disabled" in capsys.readouterr().err


def test_from_mapping_ignores_non_string_keys():
    config = Config.from_mapping({1: "ignored", "bitrate": "64k"})
    assert config.bitrate == "64k"


def test_from_mapping_with_none_uses_defaults():
    assert Config.from_mapping(None) == Config()


def test_no_legacy_config_writes_default(monkeypatch, tmp_path):
    new_dir = tmp_path / "new"
    monkeypatch.setattr(
        "convopus.config.user_config_path",
        lambda *args, **kwargs: new_dir,
    )
    monkeypatch.delenv("CONVOPUS_CONFIG")

    assert load() == Config()
    assert (new_dir / "config.json").is_file()


def test_corrupt_legacy_config_is_not_migrated(
    monkeypatch, isolated_config, tmp_path, capsys
):
    legacy_dir = tmp_path / "legacy-roaming"
    new_dir = tmp_path / "new-local"
    monkeypatch.setattr(
        "convopus.config.user_config_path",
        lambda *args, **kwargs: legacy_dir if kwargs.get("roaming") else new_dir,
    )
    monkeypatch.delenv("CONVOPUS_CONFIG")
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "config.json").write_text("{broken", encoding="utf-8")

    assert load() == Config()
    assert (new_dir / "config.json").is_file()
    assert "migrating" not in capsys.readouterr().err


def test_print_config_without_file_prints_path(isolated_config, capsys):
    assert not isolated_config.is_file()

    with pytest.raises(SystemExit) as excinfo:
        print_config(isolated_config)

    assert excinfo.value.code is None
    assert str(isolated_config) in capsys.readouterr().out
