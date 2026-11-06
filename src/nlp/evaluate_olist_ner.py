
import spacy
import pandas as pd


class NEREvaluator:
    """Evaluate NER using strict, normalized-label and text-only matching."""

    LABEL_MAPPING = {
        "PERSON": "PER",
        "PER": "PER",
        "GPE": "LOC",
        "LOC": "LOC",
        "ORG": "ORG",
        "PRODUCT": "MISC",
        "MISC": "MISC",
    }

    def __init__(self, model_name="xx_ent_wiki_sm"):
        self.model_name = model_name
        self.nlp = spacy.load(model_name)

    @staticmethod
    def calculate_metrics(tp, fp, fn):
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0

        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) else 0.0
        )

        return {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }

    def evaluate(self, samples):
        results = []

        strict_tp = strict_fp = strict_fn = 0
        normalized_tp = normalized_fp = normalized_fn = 0
        text_tp = text_fp = text_fn = 0

        for sample in samples:
            text = sample["text"]
            expected = set(sample["entities"])

            doc = self.nlp(text)

            predicted = {
                (ent.text, ent.label_)
                for ent in doc.ents
            }

            # 1. Strict evaluation: exact text and label
            strict_correct = expected & predicted
            strict_false_positives = predicted - expected
            strict_missed = expected - predicted

            strict_tp += len(strict_correct)
            strict_fp += len(strict_false_positives)
            strict_fn += len(strict_missed)

            # 2. Normalized-label evaluation
            normalized_predicted = {
                (
                    entity_text,
                    self.LABEL_MAPPING.get(label, label)
                )
                for entity_text, label in predicted
            }

            normalized_correct = expected & normalized_predicted
            normalized_false_positives = (
                normalized_predicted - expected
            )
            normalized_missed = expected - normalized_predicted

            normalized_tp += len(normalized_correct)
            normalized_fp += len(normalized_false_positives)
            normalized_fn += len(normalized_missed)

            # 3. Text-only evaluation (case-insensitive exact spans)
            expected_texts = {
                entity_text.casefold()
                for entity_text, _ in expected
            }

            predicted_texts = {
                entity_text.casefold()
                for entity_text, _ in predicted
            }

            text_correct = expected_texts & predicted_texts
            text_false_positives = predicted_texts - expected_texts
            text_missed = expected_texts - predicted_texts

            text_tp += len(text_correct)
            text_fp += len(text_false_positives)
            text_fn += len(text_missed)

            results.append({
                "review_id": sample.get("review_id", ""),
                "text": text,
                "expected": sorted(expected),
                "predicted": sorted(predicted),

                "strict_correct": sorted(strict_correct),
                "strict_false_positives": sorted(strict_false_positives),
                "strict_missed": sorted(strict_missed),

                "normalized_predicted": sorted(normalized_predicted),
                "normalized_correct": sorted(normalized_correct),
                "normalized_false_positives": sorted(
                    normalized_false_positives
                ),
                "normalized_missed": sorted(normalized_missed),

                "text_correct": sorted(text_correct),
                "text_false_positives": sorted(text_false_positives),
                "text_missed": sorted(text_missed),
            })

        return {
            "model_name": self.model_name,
            "results": results,
            "metrics": {
                "strict": self.calculate_metrics(
                    strict_tp, strict_fp, strict_fn
                ),
                "normalized": self.calculate_metrics(
                    normalized_tp, normalized_fp, normalized_fn
                ),
                "text_only": self.calculate_metrics(
                    text_tp, text_fp, text_fn
                ),
            }
        }

    def save_results(self, output, output_path):
        """Export predictions and all evaluation errors to CSV."""

        rows = []

        for result in output["results"]:
            rows.append({
                "review_id": result["review_id"],
                "text": result["text"],
                "expected": str(result["expected"]),
                "predicted": str(result["predicted"]),

                "strict_correct": str(result["strict_correct"]),
                "strict_false_positives": str(
                    result["strict_false_positives"]
                ),
                "strict_missed": str(result["strict_missed"]),

                "normalized_predicted": str(
                    result["normalized_predicted"]
                ),
                "normalized_correct": str(
                    result["normalized_correct"]
                ),
                "normalized_false_positives": str(
                    result["normalized_false_positives"]
                ),
                "normalized_missed": str(
                    result["normalized_missed"]
                ),

                "text_correct": str(result["text_correct"]),
                "text_false_positives": str(
                    result["text_false_positives"]
                ),
                "text_missed": str(result["text_missed"]),
            })

        df = pd.DataFrame(rows)

        df.to_csv(
            output_path,
            index=False,
            encoding="utf-8"
        )

        return output_path
