"""Tests for the Emergence Lab cellular automaton explorer."""
import pytest
from automaton import ElementaryCA, RuleAnalyzer, WolframClassifier, demo


class TestElementaryCA:
    """Test the core CA simulation."""

    def test_create_valid_rule(self):
        ca = ElementaryCA(110, width=20)
        assert ca.rule == 110
        assert ca.width == 20

    def test_invalid_rule_raises(self):
        with pytest.raises(ValueError):
            ElementaryCA(256)
        with pytest.raises(ValueError):
            ElementaryCA(-1)

    def test_rule_0_dies(self):
        """Rule 0: all neighborhoods map to 0. Everything dies."""
        ca = ElementaryCA(0, width=20)
        ca.state = [1] * 20
        ca.step()
        assert all(c == 0 for c in ca.state)

    def test_rule_255_fills(self):
        """Rule 255: all neighborhoods map to 1. Everything lives."""
        ca = ElementaryCA(255, width=20)
        ca.state = [0] * 20
        ca.step()
        assert all(c == 1 for c in ca.state)

    def test_single_seed_default(self):
        """Default init has single cell in center."""
        ca = ElementaryCA(110, width=11)
        assert ca.state[5] == 1
        assert sum(ca.state) == 1

    def test_run_produces_history(self):
        ca = ElementaryCA(110, width=20)
        history = ca.run(10)
        assert len(history) == 11  # initial + 10 steps
        assert all(len(row) == 20 for row in history)

    def test_deterministic_with_same_state(self):
        """Same rule + same initial state = same output."""
        ca1 = ElementaryCA(30, width=30)
        ca2 = ElementaryCA(30, width=30)
        h1 = ca1.run(20)
        h2 = ca2.run(20)
        assert h1 == h2

    def test_different_rules_differ(self):
        ca1 = ElementaryCA(30, width=30)
        ca2 = ElementaryCA(110, width=30)
        h1 = ca1.run(10)
        h2 = ca2.run(10)
        assert h1 != h2


class TestRuleAnalyzer:
    """Test entropy and complexity measurements."""

    def test_rule_0_zero_entropy(self):
        """Dead automaton has zero entropy."""
        ca = ElementaryCA(0, width=40)
        history = ca.run(20)
        analyzer = RuleAnalyzer(history)
        assert analyzer.row_entropy() < 0.01

    def test_rule_30_high_entropy(self):
        """Rule 30 (chaotic) should have high entropy."""
        ca = ElementaryCA(30, width=80)
        history = ca.run(40)
        analyzer = RuleAnalyzer(history)
        assert analyzer.row_entropy() > 0.7

    def test_compression_ratio_bounded(self):
        """Compression ratio should be between 0 and 1."""
        ca = ElementaryCA(110, width=60)
        history = ca.run(30)
        analyzer = RuleAnalyzer(history)
        ratio = analyzer.compression_ratio()
        assert 0.0 <= ratio <= 1.0

    def test_edge_of_chaos_score_bounded(self):
        ca = ElementaryCA(110, width=60)
        history = ca.run(30)
        analyzer = RuleAnalyzer(history)
        score = analyzer.edge_of_chaos_score()
        assert 0.0 <= score <= 1.0

    def test_unique_rows(self):
        ca = ElementaryCA(110, width=40)
        history = ca.run(20)
        analyzer = RuleAnalyzer(history)
        unique = analyzer.unique_row_count()
        total = len(history)
        assert 1 <= unique <= total


class TestWolframClassifier:
    """Test the automatic classification system."""

    def test_classify_single_rule(self):
        classifier = WolframClassifier()
        result = classifier.classify_rule(110, width=40, steps=20)
        assert 'wolfram_class' in result
        assert result['wolfram_class'] in (1, 2, 3, 4)
        assert 'edge_of_chaos_score' in result
        assert 'row_entropy' in result

    def test_rule_0_class_1(self):
        """Rule 0 should be Class 1 (uniform/dead)."""
        classifier = WolframClassifier()
        result = classifier.classify_rule(0, width=40, steps=20)
        assert result['wolfram_class'] == 1

    def test_classify_all_returns_256(self):
        classifier = WolframClassifier()
        results = classifier.classify_all(width=30, steps=15)
        assert len(results) == 256

    def test_all_classes_present(self):
        """The 256 rules should span multiple Wolfram classes."""
        classifier = WolframClassifier()
        results = classifier.classify_all(width=40, steps=20)
        classes = set(r['wolfram_class'] for r in results.values())
        assert len(classes) >= 3  # At least 3 of the 4 classes


class TestDemo:
    """Test the visualization function."""

    def test_demo_returns_string(self):
        result = demo(110, 30, 15)
        assert isinstance(result, str)
        assert '█' in result or '░' in result or ' ' in result

    def test_demo_contains_metrics(self):
        result = demo(110, 30, 15)
        assert 'Edge of Chaos' in result
        assert 'Entropy' in result