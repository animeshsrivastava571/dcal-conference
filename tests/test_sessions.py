from handoff.data.sessions import (
    TARGET_MAX_TURNS,
    TARGET_MIN_TURNS,
    build_sessions,
    sample_sessions,
)


def test_sessions_land_in_the_target_turn_range():
    for session in build_sessions():
        assert TARGET_MIN_TURNS <= session.n_turns <= TARGET_MAX_TURNS


def test_a_session_covers_one_company():
    for session in sample_sessions(20):
        assert {c.ticker for c in session.conversations} == {session.ticker}


def test_chaining_is_needed_to_reach_the_target():
    """A single conversation averages 3.64 turns, far below the trigger point."""
    for session in sample_sessions(20):
        assert len(session.conversations) > 1


def test_depths_are_contiguous_and_ordered():
    for session in sample_sessions(10):
        turns = session.turns
        assert [t.depth for t in turns] == list(range(len(turns)))
        assert len(turns) == session.n_turns


def test_each_conversation_starts_exactly_once():
    for session in sample_sessions(10):
        starts = [t for t in session.turns if t.starts_conversation]
        assert len(starts) == len(session.conversations)
        assert [t.conversation_index for t in starts] == list(range(len(session.conversations)))


def test_sampled_sessions_are_one_per_ticker():
    sampled = sample_sessions(30)
    assert len({s.ticker for s in sampled}) == len(sampled)


def test_conversations_are_ordered_by_year():
    for session in sample_sessions(20):
        years = [c.year for c in session.conversations]
        assert years == sorted(years)
