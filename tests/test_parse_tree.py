from analyzers.corenlp_analyzer import _parse_constituency_tree


def test_parse_constituency_tree_creates_nested_structure():
    tree = "(ROOT (S (NP (N María)) (VP (V estudia))))"
    result = _parse_constituency_tree(tree)

    assert result is not None
    assert result["label"] == "ROOT"
    assert result["children"][0]["label"] == "S"
    assert result["children"][0]["children"][0]["label"] == "NP"


def test_parse_constituency_tree_rejects_incomplete_input():
    assert _parse_constituency_tree("(ROOT (S") is None
