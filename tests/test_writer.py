"""Behaviour of the SWMM writer (``rcg.inp_manage.writer``) through ``rcg.apply``."""

from __future__ import annotations

import dataclasses
import difflib
import hashlib
import math
import os
import re
import shutil
import warnings
from pathlib import Path

import pytest
from swmmio.utils.dataframes import dataframe_from_inp

from rcg.exceptions import ModelOperationError, ValidationError
from rcg.inp_manage import writer
from rcg.service import apply

EXAMPLE_INP = Path(__file__).resolve().parent.parent / "rcg" / "example.inp"
SUBCATCHMENT_SECTIONS = ("SUBAREAS", "INFILTRATION", "Polygons", "RAINGAGES", "TIMESERIES", "SYMBOLS")


def section(path: Path, name: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return dataframe_from_inp(str(path), f"[{name}]")


def headers(path: Path) -> list[str]:
    return re.findall(r"(?m)^\s*\[([^\]]+)\]", path.read_text())


def drop_sections(text: str, names, *, keep_header: bool = False) -> str:
    for name in names:
        match = re.search(rf"(?ims)^\[{name}\].*?(?=^\[|\Z)", text)
        assert match, name
        replacement = match.group(0).splitlines(keepends=True)[0] + "\n" if keep_header else ""
        text = text[: match.start()] + replacement + text[match.end() :]
    return text


def run_swmm(path: Path) -> None:
    pyswmm = pytest.importorskip("pyswmm")
    with pyswmm.Simulation(str(path)) as sim:
        for _ in sim:
            pass


def only_insertions(before: str, after: str) -> bool:
    matcher = difflib.SequenceMatcher(None, before.splitlines(), after.splitlines(), autojunk=False)
    return all(tag in ("equal", "insert") for tag, *_ in matcher.get_opcodes())


# --------------------------------------------------------------------------- basics


def test_appends_all_four_sections(example_inp, urban_params):
    before = example_inp.read_text()
    result = apply(example_inp, urban_params, backup=False)

    assert result.subcatchment_ids == ("S16",)
    assert result.raingage == "Raingage2"
    assert result.outlet == "O4"
    assert result.output_path == example_inp

    sub = section(example_inp, "SUBCATCHMENTS").loc["S16"]
    assert (sub.Raingage, sub.Outlet) == ("Raingage2", "O4")
    assert sub.Area == 5.0
    assert sub.PercImperv == round(urban_params.impervious_pct, 2)
    assert sub.Width == 111.8
    assert sub.PercSlope == round(urban_params.slope_pct, 2)

    area = section(example_inp, "SUBAREAS").loc["S16"]
    assert (area["N-Imperv"], area["N-Perv"], area["PctZero"], area["RouteTo"]) == (0.013, 0.15, 50, "OUTLET")
    assert area["S-Imperv"] == pytest.approx(1.27)
    assert area["S-Perv"] == pytest.approx(5.08)

    infil = section(example_inp, "INFILTRATION").loc["S16"]
    assert list(infil.values) == [3.5, 0.5, 0.25, 7, 0]

    polygon = section(example_inp, "Polygons").loc["S16"]
    assert len(polygon) == 4
    side = (5.0 * 10_000) ** 0.5
    assert polygon.X.max() - polygon.X.min() == pytest.approx(side, abs=1e-3)
    assert polygon.Y.max() - polygon.Y.min() == pytest.approx(side, abs=1e-3)

    after = example_inp.read_text()
    assert only_insertions(before, after), "existing lines must be kept verbatim"
    assert headers(example_inp) == headers_of(before)


def headers_of(text: str) -> list[str]:
    return re.findall(r"(?m)^\s*\[([^\]]+)\]", text)


def test_several_subcatchments_in_one_write(example_inp, urban_params, forest_params):
    result = apply(example_inp, [urban_params, forest_params], backup=False)
    assert result.subcatchment_ids == ("S16", "S17")
    polygons = section(example_inp, "Polygons")
    # The second square starts where the first one ended (its last vertex).
    first, second = polygons.loc["S16"], polygons.loc["S17"]
    assert (second.X.iloc[0], second.Y.iloc[0]) == (first.X.iloc[-1], first.Y.iloc[-1])
    run_swmm(example_inp)


def test_ids_skip_existing_names(example_inp, urban_params, forest_params):
    text = re.sub(r"(?m)^S6(\s)", r"S16\1", example_inp.read_text())
    example_inp.write_text(text)
    result = apply(example_inp, [urban_params, forest_params], backup=False)
    assert result.subcatchment_ids == ("S17", "S18")


def test_ids_avoid_orphan_rows_in_other_sections(example_inp, urban_params):
    text = example_inp.read_text().replace("S15   3.5", "S16   3.5")
    example_inp.write_text(text)
    assert apply(example_inp, urban_params, backup=False).subcatchment_ids == ("S17",)


# --------------------------------------------------------------------------- sections


def test_upper_case_polygons_header_is_reused(example_inp, urban_params):
    example_inp.write_text(example_inp.read_text().replace("[Polygons]", "[POLYGONS]"))
    apply(example_inp, urban_params, backup=False)
    polygon_headers = [h for h in headers(example_inp) if h.upper() == "POLYGONS"]
    assert polygon_headers == ["POLYGONS"]
    assert len(section(example_inp, "Polygons").loc["S16"]) == 4
    run_swmm(example_inp)


def test_legacy_duplicate_polygons_section_is_not_multiplied(legacy_inp, urban_params):
    before = [h.upper() for h in headers(legacy_inp)].count("POLYGONS")
    apply(legacy_inp, urban_params, backup=False)
    assert [h.upper() for h in headers(legacy_inp)].count("POLYGONS") == before
    run_swmm(legacy_inp)


@pytest.mark.parametrize("keep_header", [False, True], ids=["missing", "empty"])
def test_model_without_subcatchment_sections(example_inp, urban_params, forest_params, keep_header):
    text = drop_sections(example_inp.read_text(), ("SUBCATCHMENTS", *SUBCATCHMENT_SECTIONS), keep_header=keep_header)
    example_inp.write_text(text)

    result = apply(example_inp, [urban_params, forest_params], backup=False)

    assert result.subcatchment_ids == ("S1", "S2")
    assert result.raingage == "RG1"
    assert result.outlet == "O4"
    found = [h.upper() for h in headers(example_inp)]
    for name in ("RAINGAGES", "SUBCATCHMENTS", "SUBAREAS", "INFILTRATION", "POLYGONS", "TIMESERIES"):
        assert found.count(name) == 1, name
    assert found.index("RAINGAGES") < found.index("SUBCATCHMENTS") < found.index("SUBAREAS") < found.index("INFILTRATION")
    series = section(example_inp, "TIMESERIES")
    assert list(series.index.unique()) == ["generator_series"]
    assert len(series) == len(writer.DESIGN_STORM)
    gage = section(example_inp, "RAINGAGES").loc["RG1"]
    assert gage.DataSourceName == "generator_series"
    run_swmm(example_inp)


def test_missing_subareas_infiltration_and_polygons_only(example_inp, urban_params):
    # Existing subcatchments keep their (absent) subareas; only the new one gets rows.
    text = drop_sections(example_inp.read_text(), ("SUBAREAS", "INFILTRATION", "Polygons"))
    example_inp.write_text(text)
    apply(example_inp, urban_params, backup=False)
    for name in ("SUBAREAS", "INFILTRATION", "Polygons"):
        assert list(section(example_inp, name).index.unique()) == ["S16"], name


def test_existing_raingages_are_kept(example_inp, urban_params):
    text = example_inp.read_text().replace(
        "Raingage2        INTENSITY",
        "Raingage1        VOLUME    1:00     1.0      TIMESERIES test_series\nRaingage2        INTENSITY",
        1,
    )
    example_inp.write_text(text)
    result = apply(example_inp, urban_params, backup=False)
    assert result.raingage == "Raingage1"
    assert list(section(example_inp, "RAINGAGES").index) == ["Raingage1", "Raingage2"]


def test_new_raingage_uses_first_existing_timeseries(example_inp, urban_params):
    text = drop_sections(example_inp.read_text(), ("RAINGAGES", "SYMBOLS"))
    text = re.sub(r"(?m)^(S\d+\s+)Raingage2", r"\1RG1      ", text)
    example_inp.write_text(text)
    result = apply(example_inp, urban_params, backup=False)
    assert result.raingage == "RG1"
    assert section(example_inp, "RAINGAGES").loc["RG1"].DataSourceName == "test_series"
    assert "generator_series" not in example_inp.read_text()
    run_swmm(example_inp)


def test_outlet_falls_back_to_last_junction_then_self(example_inp, urban_params):
    text = example_inp.read_text()
    no_outfalls = drop_sections(text, ("OUTFALLS",))
    example_inp.write_text(no_outfalls)
    assert apply(example_inp, urban_params, backup=False).outlet == "J3"

    example_inp.write_text(drop_sections(no_outfalls, ("JUNCTIONS",)))
    result = apply(example_inp, urban_params, backup=False)
    assert result.outlet == result.subcatchment_ids[0]
    assert section(example_inp, "SUBCATCHMENTS").loc[result.outlet].Outlet == result.outlet


def test_ids_with_leading_zeros_are_kept_verbatim(example_inp, urban_params):
    example_inp.write_text(re.sub(r"\bO4\b", "007", example_inp.read_text()))
    result = apply(example_inp, urban_params, backup=False)
    assert result.outlet == "007"
    assert re.search(r"(?m)^S16\s+Raingage2\s+007\s", example_inp.read_text())


def test_file_without_trailing_newline(example_inp, urban_params):
    example_inp.write_text(example_inp.read_text().rstrip())
    apply(example_inp, urban_params, backup=False)
    assert len(section(example_inp, "Polygons").loc["S16"]) == 4


def test_crlf_and_non_ascii_text_are_preserved(example_inp, urban_params):
    text = example_inp.read_text().replace("[TITLE]\n", "[TITLE]\nZlewnia Łódź – próbna\n", 1)
    raw = text.replace("\n", "\r\n").encode("utf-8")
    example_inp.write_bytes(raw)
    apply(example_inp, urban_params, backup=False)
    out = example_inp.read_bytes()
    assert "Zlewnia Łódź – próbna".encode() in out
    assert out.count(b"\n") == out.count(b"\r\n")
    assert out.startswith(raw[: raw.index(b"[RAINGAGES]")])


# --------------------------------------------------------------------------- safety


def test_backup_created_when_updating_in_place(example_inp, urban_params):
    original = example_inp.read_bytes()
    result = apply(example_inp, urban_params)
    assert result.backup_path is not None
    assert result.backup_path.parent == example_inp.parent / writer.BACKUP_DIR_NAME
    assert result.backup_path.name.startswith("example_backup_")
    assert result.backup_path.read_bytes() == original
    assert example_inp.read_bytes() != original


def test_written_sha256_fingerprints_the_output(example_inp, urban_params, tmp_path):
    result = apply(example_inp, urban_params, backup=False)
    assert result.written_sha256 == hashlib.sha256(example_inp.read_bytes()).hexdigest()
    out = tmp_path / "copy.inp"
    copy = apply(example_inp, urban_params, output_path=out)
    assert copy.written_sha256 == hashlib.sha256(out.read_bytes()).hexdigest()


def test_no_backup_when_opted_out(example_inp, urban_params):
    result = apply(example_inp, urban_params, backup=False)
    assert result.backup_path is None
    assert not (example_inp.parent / writer.BACKUP_DIR_NAME).exists()


def test_output_path_leaves_source_untouched(example_inp, urban_params, tmp_path):
    original = example_inp.read_bytes()
    out = tmp_path / "out" / "copy.inp"
    out.parent.mkdir()
    result = apply(example_inp, urban_params, output_path=out)
    assert example_inp.read_bytes() == original
    assert result.output_path == out
    assert result.backup_path is None
    assert "S16" in section(out, "SUBCATCHMENTS").index
    assert not (example_inp.parent / writer.BACKUP_DIR_NAME).exists()


def test_output_path_equal_to_source_counts_as_in_place(example_inp, urban_params):
    result = apply(example_inp, urban_params, output_path=str(example_inp))
    assert result.backup_path is not None


def test_existing_output_file_is_backed_up_before_it_is_replaced(example_inp, urban_params, tmp_path):
    source_bytes = example_inp.read_bytes()
    out = tmp_path / "out" / "existing.inp"
    out.parent.mkdir()
    out.write_text("old content\n")
    result = apply(example_inp, urban_params, output_path=out)
    assert result.backup_path is not None
    assert result.backup_path.parent == out.parent / writer.BACKUP_DIR_NAME
    assert result.backup_path.name.startswith("existing_backup_")
    assert result.backup_path.read_text() == "old content\n"
    assert "S16" in section(out, "SUBCATCHMENTS").index
    assert example_inp.read_bytes() == source_bytes
    assert not (example_inp.parent / writer.BACKUP_DIR_NAME).exists()


def test_existing_output_file_without_backup_when_opted_out(example_inp, urban_params, tmp_path):
    out = tmp_path / "out" / "existing.inp"
    out.parent.mkdir()
    out.write_text("old content\n")
    result = apply(example_inp, urban_params, output_path=out, backup=False)
    assert result.backup_path is None
    assert not (out.parent / writer.BACKUP_DIR_NAME).exists()
    assert "S16" in section(out, "SUBCATCHMENTS").index


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits (Windows chmod only sets read-only)")
def test_file_mode_is_preserved(example_inp, urban_params):
    os.chmod(example_inp, 0o640)
    apply(example_inp, urban_params, backup=False)
    assert example_inp.stat().st_mode & 0o777 == 0o640


def test_failed_replace_leaves_source_and_no_temp_files(example_inp, urban_params, monkeypatch):
    original = example_inp.read_bytes()

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(writer.os, "replace", boom)
    with pytest.raises(ModelOperationError, match="disk full"):
        apply(example_inp, urban_params, backup=False)
    assert example_inp.read_bytes() == original
    assert sorted(p.name for p in example_inp.parent.iterdir()) == ["example.inp"]


def test_failed_verification_writes_nothing(example_inp, urban_params, monkeypatch):
    original = example_inp.read_bytes()

    def reject(text, ids):
        raise ModelOperationError("verification failed")

    monkeypatch.setattr(writer, "_verify", reject)
    with pytest.raises(ModelOperationError, match="verification failed"):
        apply(example_inp, urban_params)
    assert example_inp.read_bytes() == original
    assert sorted(p.name for p in example_inp.parent.iterdir()) == ["example.inp"]


def test_failed_backup_writes_nothing(example_inp, urban_params, monkeypatch):
    original = example_inp.read_bytes()

    def no_backup(path):
        raise ModelOperationError("read-only folder")

    monkeypatch.setattr(writer, "create_backup", no_backup)
    with pytest.raises(ModelOperationError, match="read-only folder"):
        apply(example_inp, urban_params)
    assert example_inp.read_bytes() == original
    assert sorted(p.name for p in example_inp.parent.iterdir()) == ["example.inp"]


def test_non_utf8_model_keeps_its_bytes(example_inp, urban_params):
    text = example_inp.read_text().replace("[TITLE]\n", "[TITLE]\nZlewnia Łódź… próbna\n", 1)
    raw = text.encode("cp1250")
    example_inp.write_bytes(raw)
    apply(example_inp, urban_params, backup=False)
    out = example_inp.read_bytes()
    assert out.startswith(raw[: raw.index(b"[RAINGAGES]")])
    assert b"S16" in out
    assert only_insertions(raw.decode("cp1250"), out.decode("cp1250"))


def test_unparseable_model_is_rejected(tmp_path, urban_params):
    bad = tmp_path / "bad.inp"
    bad.write_text("[SUBCATCHMENTS]\nS1 RG1 O1 1 2 3 4 5 6 7 8 9 10 11 12\n[OPTIONS]\nthis is not\toptions\tdata at all\n")
    with pytest.raises(ModelOperationError):
        apply(bad, urban_params)


def test_missing_infiltration_keys_are_rejected(example_inp, urban_params):
    broken = dataclasses.replace(urban_params, infiltration={"Suction": 1.0})
    with pytest.raises(ModelOperationError, match="Infiltration"):
        apply(example_inp, broken, backup=False)


def test_create_backup_names_are_unique(example_inp):
    first, second = writer.create_backup(example_inp), writer.create_backup(example_inp)
    assert first != second
    assert first.read_bytes() == second.read_bytes() == example_inp.read_bytes()


@pytest.mark.parametrize(
    ("value", "expected"),
    [(5, "5"), (5.0, "5"), (0.013, "0.013"), (7.619999999999999, "7.62"), (-0.0, "0"), (777403.60679, "777403.60679")],
)
def test_number_formatting(value, expected):
    assert writer._num(value) == expected


# --------------------------------------------------------------------------- ids (case-insensitive, repeated sections)


def test_ids_are_compared_case_insensitively(example_inp, urban_params):
    # SWMM names are case-insensitive: "s16" and "S16" are the same subcatchment (ERROR 207).
    example_inp.write_text(re.sub(r"(?m)^S15(\s)", r"s16\1", example_inp.read_text()))
    result = apply(example_inp, urban_params, backup=False)
    assert result.subcatchment_ids == ("S17",)
    run_swmm(example_inp)


def test_ids_come_from_every_block_of_a_repeated_section(example_inp, urban_params):
    extra = (
        "\n[SUBCATCHMENTS]\nS16   Raingage2   J1     44.0    20  663  5  0\n"
        "[SUBAREAS]\nS16 0.15 0.41 1.27 5.08 70 OUTLET\n"
        "[INFILTRATION]\nS16 3.5 0.5 0.25 7 0\n"
    )
    example_inp.write_text(example_inp.read_text() + extra)
    result = apply(example_inp, urban_params, backup=False)
    assert result.subcatchment_ids == ("S17",)
    text = example_inp.read_text()
    assert len(re.findall(r"(?m)^S17\s+Raingage2", text)) == 1


def test_duplicate_ids_in_rendered_text_are_refused(example_inp, urban_params, monkeypatch):
    original = example_inp.read_bytes()
    monkeypatch.setattr(writer, "_new_ids", lambda doc, count: ["s15"])
    with pytest.raises(ModelOperationError, match=r"\[SUBCATCHMENTS\].*s15 \(2x\)"):
        apply(example_inp, urban_params)
    assert example_inp.read_bytes() == original
    assert sorted(p.name for p in example_inp.parent.iterdir()) == ["example.inp"]


# --------------------------------------------------------------------------- header case (swmmio verify)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("[SUBCATCHMENTS]", "[Subcatchments]"),
        ("[SUBAREAS]", "[subareas]"),
        ("[INFILTRATION]", "[Infiltration]"),
        ("[Polygons]", "[POLYGONS]"),
        ("[Polygons]", "[polygons]"),
        ("[OUTFALLS]", "[Outfalls]"),
        ("[RAINGAGES]", "[Raingages]"),
    ],
)
def test_section_headers_in_any_case_are_accepted(example_inp, urban_params, old, new):
    example_inp.write_text(example_inp.read_text().replace(old, new))
    result = apply(example_inp, urban_params, backup=False)
    assert (result.subcatchment_ids, result.raingage, result.outlet) == (("S16",), "Raingage2", "O4")
    text = example_inp.read_text()
    assert new in text, "the user's spelling of the header is kept"
    assert [h.upper() for h in headers(example_inp)].count(new.strip("[]").upper()) == 1
    if new == "[subareas]":
        run_swmm(example_inp)


# --------------------------------------------------------------------------- structural check


def test_section_sets_are_consistent():
    # A misspelt shared section would silently stay in the SWMM-only set.
    assert writer._SHARED_WITH_EPANET < writer._SWMM_SECTIONS
    assert len(writer._SWMM_ONLY_SECTIONS) == len(writer._SWMM_SECTIONS) - len(writer._SHARED_WITH_EPANET) == 42
    assert not writer._SWMM_SECTIONS & writer._EPANET_ONLY_SECTIONS


@pytest.mark.parametrize(
    ("content", "match"),
    [
        (b"hello world\nthis is not a model\n", "no SWMM section"),
        (
            b"[TITLE]\nEPANET net\n[JUNCTIONS]\n J1 100 10 ;\n[RESERVOIRS]\n R1 120\n[PIPES]\n P1 R1 J1 1000 12 100 0 Open ;\n[END]\n",
            r"EPANET network \(\[PIPES\], \[RESERVOIRS\]\)",
        ),
        (b"[TITLE]\nx\n\x00\x01\x02binary\xff\n", "binary data"),
        ("[TITLE]\n[OPTIONS]\nFLOW_UNITS CMS\n".encode("utf-16"), "UTF-16"),
        ("[TITLE]\n[OPTIONS]\nFLOW_UNITS CMS\n".encode("utf-32"), "UTF-32"),
        (b"\xfe\xff\x00[\x00T", "UTF-16"),
        (b"[TITLE]\nnet\n[JUNCTIONS]\n J1 100 10 P1\n[PATTERNS]\n P1 1.0 1.2 0.8\n", r"EPANET network \(\[PATTERNS\]\)"),
    ],
    ids=["plain-text", "epanet", "binary", "utf-16", "utf-32", "utf-16-be", "epanet-junctions-patterns"],
)
def test_files_that_are_not_swmm_models_are_refused(tmp_path, urban_params, content, match):
    path = tmp_path / "model.inp"
    path.write_bytes(content)
    with pytest.raises(ModelOperationError, match=match) as info:
        apply(path, urban_params)
    assert info.value.operation == "read"
    assert path.read_bytes() == content
    assert sorted(p.name for p in tmp_path.iterdir()) == ["model.inp"]


def test_random_bytes_are_refused(tmp_path, urban_params):
    path = tmp_path / "model.inp"
    path.write_bytes(bytes(range(256)) * 8)
    with pytest.raises(ModelOperationError, match="binary data"):
        apply(path, urban_params)


def test_swmm_model_with_some_epanet_like_section_is_accepted(example_inp, urban_params):
    example_inp.write_text(example_inp.read_text() + "\n[TANKS]\n")
    assert apply(example_inp, urban_params, backup=False).subcatchment_ids == ("S16",)


def test_minimal_model_with_title_and_options_is_accepted(tmp_path, urban_params):
    path = tmp_path / "mini.inp"
    path.write_text(
        "[TITLE]\nx\n[OPTIONS]\nFLOW_UNITS CMS\nINFILTRATION GREEN_AMPT\nSTART_DATE 01/01/2020\nEND_DATE 01/02/2020\n"
    )
    result = apply(path, urban_params, backup=False)
    assert (result.subcatchment_ids, result.raingage, result.outlet) == (("S1",), "RG1", "S1")


def test_utf8_bom_is_kept_and_first_header_recognised(example_inp, urban_params):
    raw = b"\xef\xbb\xbf" + example_inp.read_bytes()
    example_inp.write_bytes(raw)
    apply(example_inp, urban_params, backup=False)
    out = example_inp.read_bytes()
    assert out.startswith(raw[: raw.index(b"[RAINGAGES]")])
    assert out.count(b"[TITLE]") == 1


# --------------------------------------------------------------------------- paths


def test_symlinked_model_is_updated_through_the_link(tmp_path, urban_params):
    real = tmp_path / "shared" / "model.inp"
    real.parent.mkdir()
    shutil.copy2(EXAMPLE_INP, real)
    link = tmp_path / "work" / "model.inp"
    link.parent.mkdir()
    link.symlink_to(real)
    original = real.read_bytes()

    result = apply(link, urban_params)

    assert link.is_symlink() and link.resolve() == real.resolve()
    assert result.output_path == Path(os.path.realpath(real))
    assert "S16" in section(real, "SUBCATCHMENTS").index
    assert result.backup_path is not None
    assert result.backup_path.parent == Path(os.path.realpath(real.parent)) / writer.BACKUP_DIR_NAME
    assert result.backup_path.read_bytes() == original
    assert not (link.parent / writer.BACKUP_DIR_NAME).exists()
    assert sorted(p.name for p in link.parent.iterdir()) == ["model.inp"]


def test_symlinked_output_path_is_written_where_it_points(example_inp, urban_params, tmp_path):
    real = tmp_path / "real_out.inp"
    real.write_text("old\n")
    link = tmp_path / "link_out.inp"
    link.symlink_to(real)
    result = apply(example_inp, urban_params, output_path=link, backup=False)
    assert link.is_symlink()
    assert result.output_path == Path(os.path.realpath(real))
    assert "S16" in section(real, "SUBCATCHMENTS").index


@pytest.mark.skipif(not hasattr(os, "geteuid") or os.geteuid() == 0, reason="root can write read-only files")
@pytest.mark.parametrize("separate_output", [False, True], ids=["in-place", "output-path"])
def test_read_only_target_is_refused(example_inp, urban_params, tmp_path, separate_output):
    target = example_inp
    if separate_output:
        target = tmp_path / "out" / "ro.inp"
        target.parent.mkdir()
        target.write_text("old\n")
    original = target.read_bytes()
    os.chmod(target, 0o444)
    try:
        with pytest.raises(ModelOperationError, match="is read-only"):
            apply(example_inp, urban_params, output_path=target)
        assert target.read_bytes() == original
        assert not (target.parent / writer.BACKUP_DIR_NAME).exists()
        assert not list(target.parent.glob(".*.tmp"))
    finally:
        os.chmod(target, 0o644)


def test_source_changed_during_edit_is_not_overwritten(example_inp, urban_params, monkeypatch):
    real_verify = writer._verify
    meanwhile = example_inp.read_bytes() + b"\n; saved from the SWMM GUI meanwhile\n"

    def verify_then_someone_saves(text, ids):
        real_verify(text, ids)
        example_inp.write_bytes(meanwhile)

    monkeypatch.setattr(writer, "_verify", verify_then_someone_saves)
    with pytest.raises(ModelOperationError, match="changed by another program") as info:
        apply(example_inp, urban_params)
    assert info.value.operation == "write"
    assert example_inp.read_bytes() == meanwhile
    backups = example_inp.parent / writer.BACKUP_DIR_NAME
    assert not backups.exists() or not any(backups.iterdir()), "the backup made by the failed call is removed"
    assert not list(example_inp.parent.glob(".*.tmp"))


def test_source_changed_during_edit_leaves_other_target_untouched(example_inp, urban_params, tmp_path, monkeypatch):
    out = tmp_path / "out" / "copy.inp"
    out.parent.mkdir()
    out.write_text("old\n")
    real_verify = writer._verify

    def verify_then_someone_saves(text, ids):
        real_verify(text, ids)
        example_inp.write_text(example_inp.read_text() + "\n")

    monkeypatch.setattr(writer, "_verify", verify_then_someone_saves)
    with pytest.raises(ModelOperationError, match="changed by another program"):
        apply(example_inp, urban_params, output_path=out, backup=False)
    assert out.read_text() == "old\n"


# --------------------------------------------------------------------------- value checks


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"area_ha": 0.00001}, "area"),
        ({"area_ha": math.nan}, "area_ha"),
        ({"impervious_pct": 100.5}, "impervious_pct"),
        ({"impervious_pct": -1.0}, "impervious_pct"),
        ({"impervious_pct": math.nan}, "impervious_pct"),
        ({"slope_pct": -0.1}, "slope_pct"),
        ({"slope_pct": math.inf}, "slope_pct"),
        ({"width_m": 0.0}, "width_m"),
        ({"n_imperv": 0.0}, "n_imperv"),
        ({"n_perv": -0.1}, "n_perv"),
        ({"s_imperv_mm": -1.0}, "s_imperv_mm"),
        ({"s_perv_mm": math.nan}, "s_perv_mm"),
        ({"pct_zero": 101}, "pct_zero"),
        ({"pct_zero": -1}, "pct_zero"),
        ({"infiltration": {"Suction": -3.5, "Ksat": 0.5, "IMD": 0.25, "Param4": 7, "Param5": 0}}, "infiltration[Suction]"),
        ({"infiltration": {"Suction": 3.5, "Ksat": math.inf, "IMD": 0.25, "Param4": 7, "Param5": 0}}, "infiltration[Ksat]"),
    ],
)
def test_every_written_value_is_validated(example_inp, urban_params, changes, field):
    original = example_inp.read_bytes()
    with pytest.raises(ValidationError) as info:
        apply(example_inp, dataclasses.replace(urban_params, **changes))
    assert info.value.field == field
    assert example_inp.read_bytes() == original


def test_smallest_area_is_written_with_its_digits(example_inp, urban_params):
    tiny = dataclasses.replace(urban_params, area_ha=0.0001, width_m=0.5)
    apply(example_inp, tiny, backup=False)
    assert re.search(r"(?m)^S16\s+Raingage2\s+O4\s+0\.0001\s", example_inp.read_text())


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.0001, "0.0001"), (0.0001 * 2.4710538, "0.000247105"), (1.27 / 25.4, "0.05"), (5.08 / 25.4, "0.2"), (0.25, "0.25")],
)
def test_number_formatting_keeps_small_values(value, expected):
    assert writer._num(value) == expected
