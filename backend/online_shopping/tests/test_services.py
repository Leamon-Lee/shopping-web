"""Tests for service-layer components."""

import hashlib

from online_shopping.services.hash_service import generate_product_hash


class TestHashService:
    def test_generates_consistent_hash(self):
        h1 = generate_product_hash("Tote", "Bags")
        h2 = generate_product_hash("Tote", "Bags")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_case_insensitive(self):
        h1 = generate_product_hash("TOTE BAG", "BAGS")
        h2 = generate_product_hash("tote bag", "bags")
        assert h1 == h2

    def test_strips_whitespace(self):
        h1 = generate_product_hash("  Tote  ", "  Bags  ")
        h2 = generate_product_hash("Tote", "Bags")
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        h1 = generate_product_hash("Tote", "Bags")
        h2 = generate_product_hash("Mug", "Home")
        assert h1 != h2

    def test_same_name_different_category(self):
        h1 = generate_product_hash("Tote", "Bags")
        h2 = generate_product_hash("Tote", "Home")
        assert h1 != h2

    def test_matches_known_hash(self):
        expected = hashlib.sha256("tote::bags".encode("utf-8")).hexdigest()
        assert generate_product_hash("Tote", "Bags") == expected
