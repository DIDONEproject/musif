
import csv

import numpy as np
from transformers import pipeline


# Preprocess text (username and link placeholders)
def preprocess(text: str):
    new_text = []
    for t in text.split(" "):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return " ".join(new_text)

def sentiment_analysis(data: np.array):
    # Tasks:
    # emoji, emotion, hate, irony, offensive, sentiment
    # stance/abortion, stance/atheism, stance/climate, stance/feminist, stance/hillary

    sentiment_analysis = pipeline("sentiment-analysis", model="siebert/sentiment-roberta-large-english")
    result = sentiment_analysis(list(data[:, 0]))
    y = list(data[:, 1])
    preds = [obj["label"] == "POSITIVE" for obj in result]
    tp, fp, tn, fn = 0, 0, 0, 0
    for truth, pred in zip(y, preds):
        if pred and truth:
            tp += 1
        elif pred and not truth:
            fp += 1
        elif not pred and not truth:
            tn += 1
        else:
            fn += 1
    accuracy = (tp + tn) / len(preds)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1_score = (2 * precision * recall) / (precision + recall)
    print()


if __name__ == "__main__":
    with open("arias_clean_texts.csv", "r", encoding="utf-8") as csv_read_file:
        csv_reader = csv.reader(csv_read_file, delimiter=",")
        next(csv_reader)
        rows = [[row[6].replace("\n", " "), row[11] == "Positive"] for row in csv_reader]
    data = np.array(rows)
    sentiment_analysis(data)
