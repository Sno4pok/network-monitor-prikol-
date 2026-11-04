from app.database import get_stats


def print_stats(hours: int = 24) -> None:
    stats = get_stats(hours)
    if not stats:
        print("No data yet. Run: python -m app.checker")
        return

    print(f"Statistics for the last {hours} hours\n")
    print(f"{'Host':<22}{'Checks':<9}{'Uptime %':<11}{'Avg ms':<10}{'Max ms'}")
    for s in stats:
        print(
            f"{s['name']:<22}{s['total_checks']:<9}{s['uptime_percent']:<11}"
            f"{str(s['avg_response_ms']):<10}{s['max_response_ms']}"
        )


if __name__ == "__main__":
    print_stats()