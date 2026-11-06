
import spacy
import pandas as pd


class NEREvaluator:
    """Evaluate named entity recognition using a spaCy model."""

    def __init__(self, model_name="xx_ent_wiki_sm"):
        self.model_name = model_name
        self.nlp = spacy.load(model_name)

    def evaluate(self, samples):
        results = []

        total_correct = 0
        total_false_positives = 0
        total_missed = 0

        for sample in samples:
            text = sample["text"]
            expected = set(sample["entities"])

            doc = self.nlp(text)

            predicted = {
                (ent.text, ent.label_)
                for ent in doc.ents
            }

            correct = expected & predicted
            false_positives = predicted - expected
            missed = expected - predicted

            total_correct += len(correct)
            total_false_positives += len(false_positives)
            total_missed += len(missed)

            results.append({
                "review_id": sample.get("review_id", ""),
                "text": text,
                "expected": sorted(expected),
                "predicted": sorted(predicted),
                "correct": sorted(correct),
                "false_positives": sorted(false_positives),
                "missed": sorted(missed)
            })

        precision_denominator = (
            total_correct + total_false_positives
        )
        recall_denominator = (
            total_correct + total_missed
        )

        precision = (
            total_correct / precision_denominator
            if precision_denominator else 0.0
        )

        recall = (
            total_correct / recall_denominator
            if recall_denominator else 0.0
        )

        f1_score = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )

        return {
            "model_name": self.model_name,
            "results": results,
            "metrics": {
                "true_positives": total_correct,
                "false_positives": total_false_positives,
                "false_negatives": total_missed,
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score
            }
        }

    def save_results(self, output, output_path):
        """Export individual predictions and errors to CSV."""

        rows = []

        for result in output["results"]:
            rows.append({
                "review_id": result["review_id"],
                "text": result["text"],
                "expected": str(result["expected"]),
                "predicted": str(result["predicted"]),
                "correct": str(result["correct"]),
                "false_positives": str(result["false_positives"]),
                "missed": str(result["missed"])
            })

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding="utf-8")

        return output_path
