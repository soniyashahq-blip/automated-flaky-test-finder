FIX_SUGGESTIONS = {
    "sleep/time delay": "Replace fixed sleeps with explicit condition-based waits.",
    "timeout": "Use deterministic waiting and configure an appropriate timeout.",
    "randomness": "Control or seed randomness so test behavior is reproducible.",
    "date/time": "Inject or freeze the clock instead of using the current system time directly.",
    "threading/concurrency": "Synchronize shared operations and remove race conditions.",
    "shared/global state": "Reset or isolate shared state between tests.",
    "ordering dependency": "Make the test independent of execution order and isolate its setup.",
    "external dependency": "Mock or stub external services and network calls.",
    "unknown": "Inspect the test manually and reproduce the failure repeatedly.",
}


def get_fix_suggestion(category):
    return FIX_SUGGESTIONS.get(
        category,
        FIX_SUGGESTIONS["unknown"]
    )


def generate_suggestions(indicators):
    suggestions = []

    seen = set()

    for indicator in indicators:
        category = indicator["category"]

        if category not in seen:
            suggestions.append({
                "category": category,
                "suggestion": get_fix_suggestion(category)
            })
            seen.add(category)

    return suggestions