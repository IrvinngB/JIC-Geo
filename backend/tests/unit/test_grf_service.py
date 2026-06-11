from app.modules.grf.service import build_node_pairs


def test_build_node_pairs_with_waypoints() -> None:
    assert build_node_pairs(1, 4, [2, 3]) == [(1, 2), (2, 3), (3, 4)]
