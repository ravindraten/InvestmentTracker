import pytest
import json
import re
from pathlib import Path

INVEST_HTML = Path(__file__).parent.parent / "index.html"
INVEST_ORIG = Path(__file__).parent.parent / "invest.html"


def uid():
    import random
    return random.random().toString(36).slice(2, 9)


def parse_gold_grams(item):
    src = item.get("place", "")
    patterns = [
        r'(\d+(?:\.\d+)?)\s*g\b',
        r'\((\d+(?:\.\d+)?)\)',
        r'(\d+(?:\.\d+)?)\s*units',
        r'(\d+(?:\.\d+)?)\s*grams?',
        r'\b(\d+(?:\.\d+)?)$',
        r'^(\d+(?:\.\d+)?)\b',
    ]
    for pattern in patterns:
        m = re.search(pattern, src, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return 0


def eur_val(item, gold_per_gram=80, silver_per_gram=0.85):
    if item.get("category") == "gold":
        grams = parse_gold_grams(item)
        if grams > 0 and gold_per_gram > 0:
            return grams * gold_per_gram
        return float(item.get("eur") or 0)
    if item.get("category") == "silver":
        grams = parse_gold_grams(item)
        if grams > 0 and silver_per_gram > 0:
            return grams * silver_per_gram
        return float(item.get("eur") or 0)
    return float(item.get("eur") or 0)


def total_eur(items, gold_per_gram=80, silver_per_gram=0.85):
    return sum(eur_val(i, gold_per_gram, silver_per_gram) for i in items)


def total_inr(items):
    return sum(float(i.get("inr") or 0) for i in items)


def combined_eur(ravi_items, supriya_items, fx_rate=90.5, gold_per_gram=80, silver_per_gram=0.85):
    ravi_eur = total_eur(ravi_items, gold_per_gram, silver_per_gram)
    ravi_inr = total_inr(ravi_items)
    sup_eur = total_eur(supriya_items, gold_per_gram, silver_per_gram)
    sup_inr = total_inr(supriya_items)
    fx = fx_rate if fx_rate > 0 else 90.5
    return ravi_eur + sup_eur + (ravi_inr + sup_inr) / fx


def combined_inr(ravi_items, supriya_items, fx_rate=90.5, gold_per_gram=80, silver_per_gram=0.85):
    return combined_eur(ravi_items, supriya_items, fx_rate, gold_per_gram, silver_per_gram) * fx_rate


def gold_total(items):
    return sum(parse_gold_grams(i) for i in items if i.get("category") == "gold")


def validate_state(state):
    errors = []
    if not isinstance(state, dict):
        errors.append("state must be a dict")
        return errors
    if "ravi" not in state:
        errors.append("state must have 'ravi' key")
    if "supriya" not in state:
        errors.append("state must have 'supriya' key")
    for owner in ["ravi", "supriya"]:
        if owner in state:
            if not isinstance(state[owner], list):
                errors.append(f"{owner} must be a list")
            else:
                for idx, item in enumerate(state[owner]):
                    if not isinstance(item, dict):
                        errors.append(f"{owner}[{idx}] must be a dict")
                    elif "place" not in item:
                        errors.append(f"{owner}[{idx}] missing 'place'")
                    elif "category" not in item:
                        errors.append(f"{owner}[{idx}] missing 'category'")
    return errors


class TestGoldGramsParsing:
    def test_grams_with_g_suffix(self):
        assert parse_gold_grams({"place": "Solid Gold 200g"}) == 200.0

    def test_grams_in_parentheses(self):
        assert parse_gold_grams({"place": "GoldRepublic(170)"}) == 170.0

    def test_grams_with_units(self):
        assert parse_gold_grams({"place": "GoldRepublic 50 units"}) == 50.0

    def test_grams_with_grams_word(self):
        assert parse_gold_grams({"place": "Gold 100 grams"}) == 100.0

    def test_grams_at_end(self):
        assert parse_gold_grams({"place": "Holland Gold 20"}) == 20.0

    def test_grams_at_start(self):
        assert parse_gold_grams({"place": "50 Gold Coins"}) == 50.0

    def test_decimal_grams(self):
        assert parse_gold_grams({"place": "Gold 20.5g"}) == 20.5

    def test_no_grams_returns_zero(self):
        assert parse_gold_grams({"place": "Some Name"}) == 0.0


class TestEurVal:
    def test_stocks_returns_eur_field(self):
        item = {"category": "stocks", "eur": 5000, "inr": 0}
        assert eur_val(item) == 5000.0

    def test_gold_calculates_from_grams(self):
        item = {"category": "gold", "place": "Solid Gold 100g", "eur": 0}
        assert eur_val(item, gold_per_gram=80) == 8000.0

    def test_gold_falls_back_to_eur(self):
        item = {"category": "gold", "place": "NoGrams", "eur": 500, "inr": 0}
        assert eur_val(item, gold_per_gram=80) == 500.0

    def test_silver_calculates_from_grams(self):
        item = {"category": "silver", "place": "Silver 500g", "eur": 0}
        assert eur_val(item, silver_per_gram=0.85) == 425.0

    def test_missing_eur_returns_zero(self):
        item = {"category": "stocks", "place": "Test", "inr": 0}
        assert eur_val(item) == 0.0


class TestTotals:
    def test_total_eur_sums_eur_fields(self):
        items = [
            {"category": "stocks", "eur": 1000, "inr": 0},
            {"category": "stocks", "eur": 2000, "inr": 0},
        ]
        assert total_eur(items) == 3000.0

    def test_total_eur_excludes_inr(self):
        items = [
            {"category": "stocks", "eur": 1000, "inr": 100000},
        ]
        assert total_eur(items) == 1000.0

    def test_total_inr_sums_inr_fields(self):
        items = [
            {"category": "stocks", "eur": 0, "inr": 100000},
            {"category": "stocks", "eur": 0, "inr": 50000},
        ]
        assert total_inr(items) == 150000.0

    def test_gold_total_sums_grams(self):
        items = [
            {"category": "gold", "place": "Gold 100g", "eur": 0},
            {"category": "gold", "place": "Gold 50g", "eur": 0},
        ]
        assert gold_total(items) == 150.0


class TestCombinedCalculations:
    def test_combined_eur_converts_inr_to_eur(self):
        ravi = [{"category": "stocks", "eur": 1000, "inr": 9050}]
        supriya = []
        fx = 90.5
        result = combined_eur(ravi, supriya, fx_rate=fx)
        inr_in_eur = 9050 / fx
        assert result == 1000 + inr_in_eur

    def test_combined_inr_matches_eur_times_rate(self):
        ravi = [{"category": "stocks", "eur": 1000, "inr": 9050}]
        supriya = []
        fx = 90.5
        total_eur_val = combined_eur(ravi, supriya, fx_rate=fx)
        total_inr_val = combined_inr(ravi, supriya, fx_rate=fx)
        assert abs(total_inr_val - total_eur_val * fx) < 0.01


class TestStateValidation:
    def test_valid_state_passes(self):
        state = {
            "ravi": [{"place": "Test", "category": "stocks", "eur": 100}],
            "supriya": [{"place": "Test2", "category": "gold", "place": "Test 10g", "eur": 0}],
        }
        errors = validate_state(state)
        assert errors == []

    def test_missing_ravi_fails(self):
        state = {"supriya": []}
        errors = validate_state(state)
        assert "state must have 'ravi' key" in errors

    def test_missing_supriya_fails(self):
        state = {"ravi": []}
        errors = validate_state(state)
        assert "state must have 'supriya' key" in errors

    def test_item_missing_place_fails(self):
        state = {"ravi": [{"category": "stocks"}], "supriya": []}
        errors = validate_state(state)
        assert any("missing 'place'" in e for e in errors)

    def test_item_missing_category_fails(self):
        state = {"ravi": [{"place": "Test"}], "supriya": []}
        errors = validate_state(state)
        assert any("missing 'category'" in e for e in errors)


class TestHTMLStructure:
    def test_invest_shared_has_supabase_client(self):
        content = INVEST_HTML.read_text()
        assert "supabase" in content.lower() or "SB_URL" in content

    def test_invest_shared_has_no_default_data(self):
        content = INVEST_HTML.read_text()
        assert "DEFAULT_DATA" not in content
        assert "const DEFAULT_DATA" not in content

    def test_invest_html_has_default_data(self):
        if not INVEST_ORIG.exists():
            pytest.skip("invest.html not present")
        content = INVEST_ORIG.read_text()
        assert "DEFAULT_DATA" in content

    def test_invest_shared_has_auth_functions(self):
        content = INVEST_HTML.read_text()
        assert "handleLogin" in content
        assert "logout" in content
        assert "checkAuth" in content

    def test_invest_shared_has_sync_functions(self):
        content = INVEST_HTML.read_text()
        assert "initSync" in content
        assert "saveStateCloud" in content


class TestSampleData:
    @pytest.fixture
    def sample_state(self):
        return {
            "ravi": [
                {"id": "1", "place": "Trading 212", "category": "stocks", "eur": 23000, "inr": 0, "notes": ""},
                {"id": "2", "place": "Solid Gold 200g", "category": "gold", "eur": 0, "inr": 0, "notes": ""},
                {"id": "3", "place": "NPS", "category": "epf", "eur": 0, "inr": 1550000, "notes": ""},
            ],
            "supriya": [
                {"id": "4", "place": "HDFC Savings", "category": "savings", "eur": 0, "inr": 60000, "notes": ""},
                {"id": "5", "place": "Solid Gold 40g", "category": "gold", "eur": 0, "inr": 0, "notes": ""},
            ],
            "lastUpdated": "2026-04-25T09:55:15.450Z",
            "fxRate": 110
        }

    def test_sample_state_validates(self, sample_state):
        errors = validate_state(sample_state)
        assert errors == []

    def test_sample_ravi_total(self, sample_state):
        total = total_eur(sample_state["ravi"], gold_per_gram=80)
        assert total == 23000 + 16000

    def test_sample_supriya_total(self, sample_state):
        total = total_eur(sample_state["supriya"], gold_per_gram=80)
        assert total == 3200

    def test_sample_combined_eur(self, sample_state):
        fx = 110
        result = combined_eur(sample_state["ravi"], sample_state["supriya"], fx_rate=fx)
        ravi_eur = 23000 + 16000
        ravi_inr = 1550000
        sup_eur = 3200
        sup_inr = 60000
        expected = ravi_eur + sup_eur + (ravi_inr + sup_inr) / fx
        assert abs(result - expected) < 0.01


class TestEdgeCases:
    def test_empty_items_list(self):
        assert total_eur([]) == 0.0
        assert total_inr([]) == 0.0

    def test_zero_fx_rate_handled(self):
        items = [{"category": "stocks", "eur": 1000, "inr": 0}]
        combined = combined_eur(items, [], fx_rate=0)
        assert combined == 1000.0

    def test_item_with_missing_eur_and_inr(self):
        item = {"category": "stocks", "place": "Test"}
        assert eur_val(item) == 0.0
        assert total_eur([item]) == 0.0

    def test_invalid_state_type(self):
        errors = validate_state("not a dict")
        assert "state must be a dict" in errors

    def test_non_list_items(self):
        errors = validate_state({"ravi": "not a list", "supriya": []})
        assert "ravi must be a list" in errors