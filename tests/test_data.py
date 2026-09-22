import pytest

from handoff.config import MIN_YEAR_GAP
from handoff.data.convfinqa import load_conversations, parse_id
from handoff.data.pairs import sample_pairs, year_pairs
from handoff.eval.correctness import extract_number, grade, is_bare_number, is_correct

WORKED_EXAMPLE_ID = "Single_MRO/2007/page_134.pdf-1"
WORKED_EXAMPLE_ANSWERS = [60.94, 25.14, 35.8, 25.14, 1.42403]


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("ILMN/2007/page_78.pdf-2", ("ILMN", 2007)),
        ("JPM/2007/page_157.pdf-1", ("JPM", 2007)),
        ("BLK/2012/page_160.pdf-1", ("BLK", 2012)),
        ("JPM/2018/page_110.pdf-5", ("JPM", 2018)),
        (WORKED_EXAMPLE_ID, ("MRO", 2007)),
        ("Double_UPS/2009/page_33.pdf", ("UPS", 2009)),
    ],
)
def test_parse_id(raw, expected):
    assert parse_id(raw) == expected


def test_every_id_parses():
    conversations = load_conversations()
    assert len(conversations) == 3458
    assert all(c.ticker and c.year for c in conversations)


def test_documented_coverage():
    pairs = year_pairs()
    assert len(pairs) == 964
    assert len({ticker for ticker, _, _ in pairs}) == 89


def test_pairs_respect_minimum_gap():
    for pair in sample_pairs(50):
        assert pair.gap >= MIN_YEAR_GAP


def test_sampled_pairs_are_one_per_ticker():
    sampled = sample_pairs(50)
    assert len({pair.ticker for pair in sampled}) == len(sampled)


def test_worked_example_matches_documented_ground_truth():
    conversation = next(c for c in load_conversations() if c.id == WORKED_EXAMPLE_ID)
    assert conversation.ticker == "MRO"
    assert conversation.year == 2007
    assert [t.exe_ans for t in conversation.turns] == WORKED_EXAMPLE_ANSWERS
    assert conversation.turns[1].question == "and what was it in 2005?"
    # Turns 2 and 4 are arithmetic; the rest are lookups.
    assert [t.is_computed for t in conversation.turns] == [False, False, True, False, True]


def test_worked_example_grades_against_its_own_answers():
    conversation = next(c for c in load_conversations() if c.id == WORKED_EXAMPLE_ID)
    for turn in conversation.turns:
        assert is_correct(str(turn.exe_ans), turn.exe_ans)
    # The turn-1 answer must not grade as correct for turn 0.
    assert not is_correct("25.14", conversation.turns[0].exe_ans)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("$ 60.94", 60.94),
        ("1,234.5", 1234.5),
        ("The change was 35.8", 35.8),
        ("(2.5)", -2.5),
        ("142.403%", 142.403),
    ],
)
def test_extract_number(text, expected):
    parsed = extract_number(text)
    assert parsed is not None
    assert parsed[0] == pytest.approx(expected)


def test_percent_answer_matches_ratio_gold():
    assert is_correct("142.403%", 1.42403)


@pytest.mark.parametrize(
    "prediction,gold,factor",
    [
        # Reported in the table's stated units; exe_ans is absolute.
        ("1060", 1060000.0, 1e3),
        ("22", 22000000.0, 1e6),
        ("4.3", 4300.0, 1e3),
        # Percent reported bare against a ratio gold.
        ("10.465", 0.10465, 0.01),
        # Already absolute.
        ("60.94", 60.94, 1.0),
    ],
)
def test_grade_records_the_scale_factor(prediction, gold, factor):
    result = grade(prediction, gold)
    assert result.correct
    assert result.factor == pytest.approx(factor)
    assert result.exact is (factor == 1.0)


def test_grade_rejects_a_genuinely_wrong_number():
    assert not grade("25.14", 60.94).correct


HEDGED_REPLY = (
    'I cannot answer this question. "Total sum" is ambiguous without context. '
    "Based on my notes, the most recent calculation involved summing 2006 cash "
    "(104520) and 2005 cash (125385) for a total of 229905, but I don't know if "
    "that's what you're asking for."
)


@pytest.mark.parametrize(
    "text,bare",
    [
        ("60.94", True),
        (" $ 1,060 ", True),
        ("48.52%", True),
        ("(2.5)", True),
        (HEDGED_REPLY, False),
        ("I don't know", False),
        ("The answer is 60.94.", False),
    ],
)
def test_is_bare_number(text, bare):
    assert is_bare_number(text) is bare


def test_hedged_reply_is_an_abstention_not_an_answer():
    """Regression: this reply was previously mined for 229905 and scored stale."""
    result = grade(HEDGED_REPLY, 832.38)
    assert result.answered is False
    assert result.correct is False
