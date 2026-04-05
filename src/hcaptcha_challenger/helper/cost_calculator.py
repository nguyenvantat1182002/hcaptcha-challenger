# -*- coding: utf-8 -*-
import json
from pathlib import Path
from loguru import logger

DEFAULT_PRICING = {
    "pro": {"input_rate": 1.25, "output_rate": 5.00},
    "flash": {"input_rate": 0.10, "output_rate": 0.40},
    "default": {"input_rate": 0.10, "output_rate": 0.40},
}

class CostCalculator:
    def __init__(self, pricing_file: Path | None = None):
        self.pricing = DEFAULT_PRICING.copy()
        if pricing_file and pricing_file.exists():
            try:
                custom_pricing = json.loads(pricing_file.read_text(encoding="utf-8"))
                self.pricing.update(custom_pricing)
                logger.debug(f"Loaded custom pricing from {pricing_file}")
            except Exception as e:
                logger.warning(f"Failed to load custom pricing: {e}, using defaults")

    def calculate(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        # Find the best match for the model name
        rate_info = self.pricing.get("default")
        
        # Exact match check
        if model_name in self.pricing:
            rate_info = self.pricing[model_name]
        else:
            # Partial match check (e.g., 'gemini-1.5-pro' matches 'gemini-1.5-pro' if defined, or contains 'pro')
            for key, value in self.pricing.items():
                if key != "default" and key in model_name.lower():
                    rate_info = value
                    break

        input_rate = rate_info.get("input_rate", 0.10) / 1_000_000
        output_rate = rate_info.get("output_rate", 0.40) / 1_000_000
        
        return (prompt_tokens * input_rate) + (completion_tokens * output_rate)
