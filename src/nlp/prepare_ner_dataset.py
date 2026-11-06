
import pandas as pd
from pathlib import Path


DATA_PATH = (
    "datasets/processed/olist/"
    "olist_order_reviews_dataset.parquet"
)

ANNOTATED_PATH = (
    "datasets/processed/olist/"
    "ner_annotation_template_corrected.csv"
)

OUTPUT_PATH = (
    "datasets/processed/olist/"
    "ner_annotation_batch_02.csv"
)

BATCH_SIZE = 200
RANDOM_STATE = 123


def main():
    df = pd.read_parquet(DATA_PATH)

    df["review_text"] = (
        df["review_comment_title"].fillna("").astype(str).str.strip()
        + " "
        + df["review_comment_message"].fillna("").astype(str).str.strip()
    ).str.strip()

    # Keep reviews containing actual text
    df = df[df["review_text"] != ""].copy()

    # Exclude reviews already present in the corrected annotation file
    annotated = pd.read_csv(ANNOTATED_PATH)

    existing_ids = set(
        annotated["review_id"].astype(str)
    )

    df["review_id"] = df["review_id"].astype(str)

    available = df[
        ~df["review_id"].isin(existing_ids)
    ].copy()

    if len(available) < BATCH_SIZE:
        raise ValueError(
            f"Only {len(available)} unannotated reviews available"
        )

    # Select a reproducible new batch
    sample = available.sample(
        n=BATCH_SIZE,
        random_state=RANDOM_STATE
    )

    annotation = pd.DataFrame({
        "review_id": sample["review_id"],
        "review_text": sample["review_text"],
        "entities": "[]"
    })

    # Save without overwriting the previous batch
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    annotation.to_csv(
        output_path,
        index=False,
        encoding="utf-8"
    )

    print("New NER annotation batch created.")
    print("Total reviews:", len(annotation))
    print("Previously annotated reviews excluded:", len(existing_ids))
    print("Remaining available reviews:", len(available))
    print("Output:", OUTPUT_PATH)
    print("\nPreview:")
    print(annotation.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
