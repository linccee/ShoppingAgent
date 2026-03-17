import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent.nodes import _rank_products, currency_node, search_node


class StateGraphNodeTests(unittest.TestCase):
    def test_search_node_treats_tool_failure_as_workflow_error(self):
        state = {"user_query": "headphones", "steps": []}

        with patch(
            "tools.search_tool.search_products",
            new=SimpleNamespace(
                invoke=lambda _query: json.dumps(
                    {"success": False, "error": "missing serpapi key", "results": []},
                    ensure_ascii=False,
                )
            ),
        ):
            result = search_node(state)

        self.assertEqual(result["workflow_status"], "error")
        self.assertIn("missing serpapi key", result["error_message"])
        self.assertEqual(result["steps"][-1]["status"], "error")

    def test_currency_node_uses_tool_contract_and_reads_conversion_result(self):
        state = {"user_query": "预算 ¥3000 的耳机", "steps": []}
        mock_tool = SimpleNamespace(
            invoke=unittest.mock.Mock(
                return_value=json.dumps(
                    {"success": True, "conversion_result": 412.5},
                    ensure_ascii=False,
                )
            )
        )

        with patch(
            "tools.currency_exchange_tool.currency_exchange",
            new=mock_tool,
        ):
            result = currency_node(state)

        mock_tool.invoke.assert_called_once_with(
            {
                "amount": "3000.0",
                "base_code": "CNY",
                "target_code": "USD",
            }
        )
        self.assertEqual(result["currency_result"]["converted_amount"], 412.5)
        self.assertEqual(result["steps"][-1]["status"], "completed")

    def test_rank_products_prefers_higher_scored_candidates_and_reassigns_rank(self):
        candidates = [
            {"title": "A", "product_sku": "sku-a", "url": "url-a"},
            {"title": "B", "product_sku": "sku-b", "url": "url-b"},
            {"title": "C", "product_sku": "sku-c", "url": "url-c"},
        ]
        prices = [
            {
                "title": "B",
                "product_sku": "sku-b",
                "platform": "Amazon",
                "price": {"amount": "$200", "currency": "USD"},
                "url": "url-b",
            },
            {
                "title": "C",
                "product_sku": "sku-c",
                "platform": "Amazon",
                "price": {"amount": "$300", "currency": "USD"},
                "url": "url-c",
            },
        ]
        reviews = [
            {"product_sku": "sku-b", "sentiment": "positive"},
            {"product_sku": "sku-c", "sentiment": "neutral"},
        ]

        ranked = _rank_products(candidates, prices, reviews)

        self.assertEqual(
            [item["product"]["product_sku"] for item in ranked],
            ["sku-b", "sku-c", "sku-a"],
        )
        self.assertEqual([item["rank"] for item in ranked], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
