"""Row 708 Code Formatting : four mechanical layout checks on supplied source lines.

check(lines, max_width, indent) takes 1..500 strings of 0..300 characters with no line breaks, max_width 20..200
and indent 1..8 (whole numbers). Per line, in this order of kinds:
  too_long             len(line) > max_width, counting characters (not display columns);
  trailing_whitespace  the line has other text and ends with an ASCII space or tab;
  tab_indent           the leading run of ASCII spaces and tabs contains a tab, on a line with other text;
  bad_indent           no tab in that run, the line has other text, and its count of leading ASCII spaces is
                       not a multiple of indent.
Other whitespace such as U+00A0 is ordinary text for these checks. Violations are (line_index, kind) sorted by
index then the kind order above. These checks and ranges are this module's own choices, not a style guide. It
counts characters in supplied text. It parses no language, rewrites nothing and judges no style."""
MAX_LINES, MAX_LINE = 500, 300
KINDS = ("too_long", "trailing_whitespace", "tab_indent", "bad_indent")
NOT_CLAIMED = ("a style guide", "language syntax", "display width of wide characters",
               "readability", "runtime behaviour")
_BLANKS = " \t"


def check(lines, max_width, indent):
    if type(lines) is not list or not 1 <= len(lines) <= MAX_LINES:
        raise ValueError(f"lines: list of 1 to {MAX_LINES} required")
    for i, s in enumerate(lines):
        if type(s) is not str or len(s) > MAX_LINE or "\n" in s or "\r" in s:
            raise ValueError(f"lines[{i}]: string of 0 to {MAX_LINE} characters without line breaks required")
    if type(max_width) is not int or not 20 <= max_width <= 200:
        raise ValueError("max_width: whole number 20 to 200 required")
    if type(indent) is not int or not 1 <= indent <= 8:
        raise ValueError("indent: whole number 1 to 8 required")
    violations = []
    for i, s in enumerate(lines):
        text = s.lstrip(_BLANKS)
        lead = s[:len(s) - len(text)]
        if len(s) > max_width:
            violations.append((i, "too_long"))
        if text and s != s.rstrip(_BLANKS):
            violations.append((i, "trailing_whitespace"))
        if text and "\t" in lead:
            violations.append((i, "tab_indent"))
        elif text and len(lead) % indent:
            violations.append((i, "bad_indent"))
    return {"violations": violations, "clean": not violations,
            "formatting_validated": False, "not_claimed": NOT_CLAIMED}
