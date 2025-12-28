"""Tests for config module."""

import os
import tempfile
import unittest
from pathlib import Path

import config


class TestConfig(unittest.TestCase):
    """Test configuration loading and validation."""

    def setUp(self):
        """Clear environment before each test."""
        for key in list(os.environ.keys()):
            if (
                key.startswith("PORT")
                or key.startswith("BACKEND_URL")
                or key.startswith("LOG_LEVEL")
            ):
                del os.environ[key]

    def test_load_default_config(self):
        """Test loading config with no env vars set."""
        cfg = config.load_config()

        self.assertEqual(cfg["port"], 4242)
        self.assertEqual(cfg["backend_url"], "https://opencode.ai/zen/v1")
        self.assertEqual(cfg["log_level"], "INFO")

    def test_load_config_from_env_vars(self):
        """Test loading config from environment variables."""
        os.environ["PORT"] = "8080"
        os.environ["BACKEND_URL"] = "http://localhost:8080/v1"
        os.environ["LOG_LEVEL"] = "DEBUG"

        cfg = config.load_config()

        self.assertEqual(cfg["port"], 8080)
        self.assertEqual(cfg["backend_url"], "http://localhost:8080/v1")
        self.assertEqual(cfg["log_level"], "DEBUG")

    def test_invalid_port_defaults_to_4242(self):
        """Test that invalid PORT defaults to 4242."""
        os.environ["PORT"] = "invalid"

        cfg = config.load_config()

        self.assertEqual(cfg["port"], 4242)

    def test_invalid_log_level_defaults_to_info(self):
        """Test that invalid LOG_LEVEL defaults to INFO."""
        os.environ["LOG_LEVEL"] = "INVALID"

        cfg = config.load_config()

        self.assertEqual(cfg["log_level"], "INFO")

    def test_is_zen_backend(self):
        """Test zen backend detection."""
        self.assertTrue(config.is_zen_backend("https://opencode.ai/zen/v1"))
        self.assertTrue(config.is_zen_backend("https://opencode.ai/zen/v1/models"))

        self.assertFalse(config.is_zen_backend("http://localhost:8080/v1"))
        self.assertFalse(config.is_zen_backend("http://localhost:8080"))
        self.assertFalse(config.is_zen_backend("https://api.openai.com/v1"))

    def test_config_returns_dict(self):
        """Test that load_config returns a dict with expected keys."""
        cfg = config.load_config()

        self.assertIsInstance(cfg, dict)
        self.assertIn("port", cfg)
        self.assertIn("backend_url", cfg)
        self.assertIn("log_level", cfg)


if __name__ == "__main__":
    unittest.main()
