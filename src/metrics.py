from src.models import CategorizationResult

def run_summary(results: list[CategorizationResult]) -> dict:
    item = {
        "total": 0,
        "by_source": {"keyword": 0, "claude": 0},
        "input_tokens": 0,
        "output_tokens": 0
    }
    for result in results:
        if result.source == 'keyword':
            item["by_source"]["keyword"] += 1
        else: 
            item["by_source"]["claude"] += 1
        item["input_tokens"] += result.input_tokens
        item["output_tokens"] += result.output_tokens
    item["total"] = item["by_source"]["keyword"] + item["by_source"]["claude"]

    return item