"""AUTHORED, NOT RUN. H04: load_profiles raises only ProviderError for bad SUGARCODE_MODEL_PROFILES.
Written before the code change. Parent: H04a V3 (b6333171) with decode_strict_json."""
import json
import traceback

import pytest

from sugarcode.llm import providers as P

GOOD = {"name": "lab-box", "base_url": "http://10.0.0.5:9000/v1", "model": "m", "kind": "self_hosted"}
ENV = "SUGARCODE_MODEL_PROFILES"


def env_of(value):
    return {ENV: value if isinstance(value, str) else json.dumps(value)}


def bad(value):
    with pytest.raises(P.ProviderError) as e:
        P.load_profiles(env_of(value))
    assert type(e.value) is P.ProviderError
    return str(e.value)


def test_valid_list_inline_still_loads_and_keeps_builtins():
    out = P.load_profiles(env_of([GOOD]))
    assert out["lab-box"].base_url == "http://10.0.0.5:9000/v1"
    assert set(P.BUILTIN_PROFILES) <= set(out)


def test_valid_list_from_file_still_loads(tmp_path):
    f = tmp_path / "profiles.json"
    f.write_text(json.dumps([GOOD]))
    assert "lab-box" in P.load_profiles({ENV: str(f)})


def test_empty_env_and_unset_unchanged():
    assert set(P.load_profiles({})) == set(P.BUILTIN_PROFILES)
    assert set(P.load_profiles({ENV: "   "})) == set(P.BUILTIN_PROFILES)


def test_empty_list_is_valid_and_adds_nothing():
    assert set(P.load_profiles(env_of("[]"))) == set(P.BUILTIN_PROFILES)


def test_missing_file_is_provider_error_not_oserror(tmp_path):
    with pytest.raises(P.ProviderError) as e:
        P.load_profiles({ENV: str(tmp_path / "nope.json")})
    assert type(e.value) is P.ProviderError


def test_directory_path_is_provider_error(tmp_path):
    with pytest.raises(P.ProviderError):
        P.load_profiles({ENV: str(tmp_path)})


def test_undecodable_file_is_provider_error(tmp_path):
    f = tmp_path / "bin.json"
    f.write_bytes(b"\xff\xfe\x00[")
    with pytest.raises(P.ProviderError):
        P.load_profiles({ENV: str(f)})


def test_nul_in_path_is_provider_error():
    with pytest.raises(P.ProviderError):
        P.load_profiles({ENV: "a\x00b"})


@pytest.mark.parametrize("text", ["[", "[1,]", "[] x", "[NaN]", "[1e999]",
                                  '[{"name": "a", "name": "b"}]'])
def test_strict_json_failures_are_provider_error(text):
    bad(text)


def test_non_list_top_level_via_file_is_provider_error(tmp_path):
    for body in ('{"name": "x"}', "3", '"x"', "null", "true"):
        f = tmp_path / "p.json"
        f.write_text(body)
        with pytest.raises(P.ProviderError) as e:
            P.load_profiles({ENV: str(f)})
        assert type(e.value) is P.ProviderError


def test_blank_file_is_provider_error_not_empty_list(tmp_path):
    f = tmp_path / "blank.json"
    f.write_text("   \n")
    with pytest.raises(P.ProviderError):
        P.load_profiles({ENV: str(f)})


def test_oversized_text_is_provider_error(tmp_path):
    f = tmp_path / "big.json"
    f.write_text("[" + " " * 70_000 + "]")
    with pytest.raises(P.ProviderError):
        P.load_profiles({ENV: str(f)})


def test_too_deep_is_provider_error():
    bad("[" * 70 + "]" * 70)


@pytest.mark.parametrize("item", [1, "x", None, [1], True, 1.5])
def test_non_dict_element_is_provider_error(item):
    bad([item])


def test_unknown_field_is_provider_error_and_names_the_field():
    msg = bad([dict(GOOD, color="red")])
    assert "color" in msg


@pytest.mark.parametrize("drop", ["name", "base_url", "model", "kind"])
def test_missing_required_field_is_provider_error(drop):
    item = {k: v for k, v in GOOD.items() if k != drop}
    assert drop in bad([item])


def test_invalid_kind_and_transport_still_provider_error():
    bad([dict(GOOD, kind="cloud")])
    bad([dict(GOOD, transport="grpc")])


@pytest.mark.parametrize("name", [["x"], {"a": 1}])
def test_unhashable_name_is_provider_error(name):
    bad([dict(GOOD, name=name)])


@pytest.mark.parametrize("name", sorted(P.BUILTIN_PROFILES))
def test_shadowing_a_builtin_is_refused(name):
    msg = bad([dict(GOOD, name=name)])
    assert name in msg


def test_shadow_refusal_leaves_no_partial_result():
    with pytest.raises(P.ProviderError):
        P.load_profiles(env_of([GOOD, dict(GOOD, name="ollama")]))


def test_error_does_not_echo_raw_input_or_file_contents(tmp_path):
    secret = "SECRET-TOKEN-123"
    f = tmp_path / "s.json"
    f.write_text('[{"name": "x", "base_url": "u", "model": "m", "kind": "cloud", "api_key_env": "%s", "zzz": 1}]' % secret)
    with pytest.raises(P.ProviderError) as e:
        P.load_profiles({ENV: str(f)})
    assert secret not in str(e.value)
    with pytest.raises(P.ProviderError) as e2:
        P.load_profiles({ENV: '[{"a": "%s", "a": 2}]' % secret})
    assert secret not in str(e2.value)


def test_codec_reason_is_in_the_message_for_strict_failures():
    assert "duplicate_key" in bad('[{"a": 1, "a": 2}]')
    assert "non_finite" in bad("[NaN]")
    assert "invalid_json" in bad("[")


def test_duplicate_custom_names_keep_last_as_before():
    out = P.load_profiles(env_of([dict(GOOD, model="first"), dict(GOOD, model="second")]))
    assert out["lab-box"].model == "second"


# ---- route-parse escape closes as typed ProviderError ----
def test_parse_route_resolve_resolve_route_and_status_raise_provider_error():
    env = {ENV: '{"x"'}
    for call in (lambda: P.parse_route(env=env), lambda: P.resolve("ollama", env=env),
                 lambda: P.resolve_route(env=env), lambda: P.profile_status(env=env)):
        with pytest.raises(P.ProviderError) as e:
            call()
        assert type(e.value) is P.ProviderError


def test_route_with_non_list_and_bad_element_files_are_provider_error(tmp_path):
    f = tmp_path / "p.json"
    f.write_text("[1]")
    with pytest.raises(P.ProviderError):
        P.parse_route(env={ENV: str(f)})
    f.write_text("{}")
    with pytest.raises(P.ProviderError):
        P.resolve_route(env={ENV: str(f)})


# ---- custom profile names are never echoed, on any path, including cause/context/traceback ----
SECRET_NAME = "SECRET-PROFILE-NAME-xyz"


def _no_name_anywhere(exc, name):
    assert name not in str(exc)
    assert name not in repr(exc)
    assert exc.__cause__ is None
    assert exc.__context__ is None
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    assert name not in tb


@pytest.mark.parametrize("field,value", [("kind", "cloud"), ("transport", "grpc")])
def test_secret_custom_name_not_leaked_by_invalid_kind_or_transport(field, value):
    with pytest.raises(P.ProviderError) as e:
        P.load_profiles(env_of([dict(GOOD, name=SECRET_NAME, **{field: value})]))
    assert type(e.value) is P.ProviderError
    _no_name_anywhere(e.value, SECRET_NAME)
    assert "item 0" in str(e.value)


def test_secret_name_not_leaked_via_other_failure_paths():
    for item in (dict(GOOD, name=SECRET_NAME, bogus=1),
                 {k: v for k, v in dict(GOOD, name=SECRET_NAME).items() if k != "model"}):
        with pytest.raises(P.ProviderError) as e:
            P.load_profiles(env_of([item]))
        _no_name_anywhere(e.value, SECRET_NAME)


def test_secret_name_with_valid_profile_still_loads():
    assert SECRET_NAME in P.load_profiles(env_of([dict(GOOD, name=SECRET_NAME)]))
