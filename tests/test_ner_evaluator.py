import unittest

from src.nlp.ner_evaluator import NEREvaluator


class TestNEREvaluator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.evaluator = NEREvaluator()

    def test_evaluator_returns_results_and_metrics(self):
        samples = [
            {
                "text": "A Samsung product arrived in São Paulo.",
                "entities": [
                    ("São Paulo", "LOC")
                ]
            }
        ]

        output = self.evaluator.evaluate(samples)

        self.assertIn("results", output)
        self.assertIn("metrics", output)
        self.assertEqual(len(output["results"]), 1)

    def test_metrics_contain_required_values(self):
        samples = [
            {
                "text": "O vendedor João enviou o pedido.",
                "entities": [
                    ("João", "PER")
                ]
            }
        ]

        output = self.evaluator.evaluate(samples)
        metrics = output["metrics"]

        required_keys = [
            "true_positives",
            "false_positives",
            "false_negatives",
            "precision",
            "recall",
            "f1_score"
        ]

        for key in required_keys:
            self.assertIn(key, metrics)

        for key in ["precision", "recall", "f1_score"]:
            self.assertGreaterEqual(metrics[key], 0.0)
            self.assertLessEqual(metrics[key], 1.0)

    def test_empty_samples(self):
        output = self.evaluator.evaluate([])

        self.assertEqual(output["results"], [])
        self.assertEqual(output["metrics"]["true_positives"], 0)
        self.assertEqual(output["metrics"]["precision"], 0.0)
        self.assertEqual(output["metrics"]["recall"], 0.0)
        self.assertEqual(output["metrics"]["f1_score"], 0.0)


if __name__ == "__main__":
    unittest.main()