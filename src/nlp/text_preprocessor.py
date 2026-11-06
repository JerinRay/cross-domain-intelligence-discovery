
import re
import pandas as pd


class TextPreprocessor:
    """Clean and normalize text for downstream NLP tasks."""

    def preprocess(self, text):
        """
        Clean one text value.

        Returns an empty string for missing or non-text input.
        Preserves Portuguese accented characters.
        """

        # Handle missing and non-string values
        if not isinstance(text, str):
            return ""

        text = text.strip()

        if not text:
            return ""

        # Convert text to lowercase
        text = text.lower()

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Remove URLs
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)

        # Replace punctuation and special characters with spaces
        # Preserve Unicode letters, numbers and whitespace
        text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

        # Remove underscores
        text = text.replace("_", " ")

        # Normalize multiple spaces and line breaks
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def preprocess_dataframe(
        self,
        data,
        text_column,
        output_column="processed_text"
    ):
        """Add cleaned text while preserving original columns."""

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")

        if data.empty:
            raise ValueError("Input DataFrame cannot be empty")

        if text_column not in data.columns:
            raise ValueError(
                f"Column '{text_column}' not found in DataFrame"
            )

        result = data.copy()

        # Explicitly handle NaN and None values
        result[output_column] = result[text_column].apply(
            lambda value: self.preprocess(
                "" if pd.isna(value) else value
            )
        )

        return result
