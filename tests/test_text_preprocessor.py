  
import unittest
import pandas as pd

from src.nlp.text_preprocessor import TextPreprocessor


class TestTextPreprocessor(unittest.TestCase):

    def setUp(self):
        self.processor = TextPreprocessor()

    def test_lowercase_conversion(self):
        result = self.processor.preprocess("ÓTIMO PRODUTO")
        self.assertEqual(result, "ótimo produto")

    def test_portuguese_accents_preserved(self):
        result = self.processor.preprocess("Não gostei da entrega")
        self.assertEqual(result, "não gostei da entrega")

    def test_punctuation_removal(self):
        result = self.processor.preprocess("Produto ótimo!!!")
        self.assertEqual(result, "produto ótimo")

    def test_html_removal(self):
        result = self.processor.preprocess(
            "<p>Produto excelente!</p>"
        )
        self.assertEqual(result, "produto excelente")

    def test_url_removal(self):
        result = self.processor.preprocess(
            "Visit https://example.com for details"
        )
        self.assertEqual(result, "visit for details")

    def test_missing_text(self):
        self.assertEqual(self.processor.preprocess(None), "")

    def test_empty_text(self):
        self.assertEqual(self.processor.preprocess("   "), "")

    def test_non_string_input(self):
        self.assertEqual(self.processor.preprocess(123), "")

    def test_dataframe_preserves_original_columns(self):
        df = pd.DataFrame({
            "review_id": ["R1", "R2"],
            "review_comment": ["Ótimo produto!", "Não gostei."]
        })

        result = self.processor.preprocess_dataframe(
            df,
            "review_comment"
        )

        self.assertIn("review_comment", result.columns)
        self.assertIn("processed_text", result.columns)
        self.assertEqual(
            result["processed_text"].tolist(),
            ["ótimo produto", "não gostei"]
        )

    def test_missing_column_raises_error(self):
        df = pd.DataFrame({"review": ["Good"]})

        with self.assertRaises(ValueError):
            self.processor.preprocess_dataframe(
                df,
                "missing_column"
            )

    def test_invalid_dataframe_raises_error(self):
        with self.assertRaises(TypeError):
            self.processor.preprocess_dataframe(
                ["not", "a dataframe"],
                "review"
            )

    def test_empty_dataframe_raises_error(self):
        df = pd.DataFrame(columns=["review"])

        with self.assertRaises(ValueError):
            self.processor.preprocess_dataframe(
                df,
                "review"
            )


if __name__ == "__main__":
    unittest.main()
