from clipscribe.utils.stable_id import generate_stable_id, generate_unversioned_digest


def test_generate_stable_id_prefix_and_length():
    sid = generate_stable_id("hello", algo="sha256", length=20)
    assert sid.startswith("sha256-20-")
    assert len(sid.split("-")[-1]) == 20


def test_generate_unversioned_digest_sha256():
    d = generate_unversioned_digest("hello", algo="sha256", length=16)
    assert len(d) == 16
    # Stable across calls
    assert d == generate_unversioned_digest("hello", algo="sha256", length=16)


def test_generate_unversioned_digest_blake2b():
    d = generate_unversioned_digest("hello", algo="blake2b", length=16)
    assert len(d) == 16
    assert d == generate_unversioned_digest("hello", algo="blake2b", length=16)


