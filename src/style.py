from __future__ import annotations

import questionary

CYAN = "#00d7ff"

QUESTIONARY_STYLE: questionary.Style = questionary.Style(
    [
        ("qmark", f"fg:{CYAN} bold"),
        ("question", "bold"),
        ("answer", f"fg:{CYAN} bold"),
        ("pointer", f"fg:{CYAN} bold"),
        ("highlighted", f"fg:{CYAN} bold"),
        ("selected", f"fg:{CYAN}"),
        ("instruction", "fg:#888888"),
        ("disabled", "fg:#666666 italic"),
    ]
)
