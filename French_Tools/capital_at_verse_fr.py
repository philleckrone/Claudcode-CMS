# -*- coding: utf-8 -*-
import checking
import os
import re
import sys as _sys
import traceback
import unicodedata
import xml.etree.ElementTree as ET

# Optional helper from the cms folder (ptx_goto.py): makes the references in
# the HTML report clickable. Without it the references stay plain text.
try:
    import ptx_goto as _ptx_goto
except Exception:
    _ptx_goto = None
_links_on = False

def _goto(ref):
    return _ptx_goto.target(ref) if _links_on else None

def _ref_link(ref_html, tgt):
    return _ptx_goto.link(ref_html, tgt) if _links_on and tgt else ref_html

# Guard option variable injected by Paratext.
try:
    FinalPunctuation
except NameError:
    FinalPunctuation = '.!?'

if not isinstance(FinalPunctuation, type(u'')):
    try:
        FinalPunctuation = FinalPunctuation.decode('utf-8')
    except UnicodeDecodeError:
        FinalPunctuation = FinalPunctuation.decode('mbcs')
_final_set = set(FinalPunctuation)

try:
    WordsToIgnore
except NameError:
    WordsToIgnore = ''
if not isinstance(WordsToIgnore, type(u'')):
    try:
        WordsToIgnore = WordsToIgnore.decode('utf-8')
    except UnicodeDecodeError:
        WordsToIgnore = WordsToIgnore.decode('mbcs')
_ignore_words = frozenset(unicodedata.normalize('NFC', w.strip()) for w in WordsToIgnore.split(u',') if w.strip())
_ignore_words_lower = frozenset(w.lower() for w in _ignore_words)

try:
    IgnoreCapAfterQuote
except NameError:
    IgnoreCapAfterQuote = 'No'
if not isinstance(IgnoreCapAfterQuote, type(u'')):
    try:
        IgnoreCapAfterQuote = IgnoreCapAfterQuote.decode('utf-8')
    except UnicodeDecodeError:
        IgnoreCapAfterQuote = IgnoreCapAfterQuote.decode('mbcs')
_ignore_cap_after_quote = IgnoreCapAfterQuote.strip().lower() == u'yes'

try:
    IgnoreBiblicalTerms
except NameError:
    IgnoreBiblicalTerms = 'Yes'
if not isinstance(IgnoreBiblicalTerms, type(u'')):
    try:
        IgnoreBiblicalTerms = IgnoreBiblicalTerms.decode('utf-8')
    except UnicodeDecodeError:
        IgnoreBiblicalTerms = IgnoreBiblicalTerms.decode('mbcs')
_ignore_bt = IgnoreBiblicalTerms.strip().lower() == u'yes'

try:
    IgnoreWordlistCapitals
except NameError:
    IgnoreWordlistCapitals = 'Yes'
if not isinstance(IgnoreWordlistCapitals, type(u'')):
    try:
        IgnoreWordlistCapitals = IgnoreWordlistCapitals.decode('utf-8')
    except UnicodeDecodeError:
        IgnoreWordlistCapitals = IgnoreWordlistCapitals.decode('mbcs')
_ignore_wordlist = IgnoreWordlistCapitals.strip().lower() == u'yes'

# Optional names dictionary (off while NamesDictionaryFile is empty).
try:
    NamesDictionaryFile
except NameError:
    NamesDictionaryFile = ''
if not isinstance(NamesDictionaryFile, type(u'')):
    try:
        NamesDictionaryFile = NamesDictionaryFile.decode('utf-8')
    except UnicodeDecodeError:
        NamesDictionaryFile = NamesDictionaryFile.decode('mbcs')

try:
    NamesDictionaryMarkers
except NameError:
    NamesDictionaryMarkers = 'lx'
if not isinstance(NamesDictionaryMarkers, type(u'')):
    try:
        NamesDictionaryMarkers = NamesDictionaryMarkers.decode('utf-8')
    except UnicodeDecodeError:
        NamesDictionaryMarkers = NamesDictionaryMarkers.decode('mbcs')

try:
    NamesDictionaryAllowSuffixes
except NameError:
    NamesDictionaryAllowSuffixes = 'No'
if not isinstance(NamesDictionaryAllowSuffixes, type(u'')):
    try:
        NamesDictionaryAllowSuffixes = NamesDictionaryAllowSuffixes.decode('utf-8')
    except UnicodeDecodeError:
        NamesDictionaryAllowSuffixes = NamesDictionaryAllowSuffixes.decode('mbcs')
_dic_allow_suffixes = NamesDictionaryAllowSuffixes.strip().lower() == u'yes'

try:
    QuoteOpeningChars
except NameError:
    QuoteOpeningChars = unichr(0x00ab) + unichr(0x201c) + unichr(0x2014) + unichr(0x2018)
if not isinstance(QuoteOpeningChars, type(u'')):
    try:
        QuoteOpeningChars = QuoteOpeningChars.decode('utf-8')
    except UnicodeDecodeError:
        QuoteOpeningChars = QuoteOpeningChars.decode('mbcs')
_quote_openers = frozenset(QuoteOpeningChars.strip()) if QuoteOpeningChars.strip() else None

try:
    IgnoreStyles
except NameError:
    IgnoreStyles = 'qs'
if not isinstance(IgnoreStyles, type(u'')):
    try:
        IgnoreStyles = IgnoreStyles.decode('utf-8')
    except UnicodeDecodeError:
        IgnoreStyles = IgnoreStyles.decode('mbcs')
_ignore_style_names = [s.strip().lstrip(u'\\') for s in IgnoreStyles.split(u',') if s.strip()]

try:
    IgnoreParaStyles
except NameError:
    IgnoreParaStyles = 'sp, r, ms, mr, sr, qa'
if not isinstance(IgnoreParaStyles, type(u'')):
    try:
        IgnoreParaStyles = IgnoreParaStyles.decode('utf-8')
    except UnicodeDecodeError:
        IgnoreParaStyles = IgnoreParaStyles.decode('mbcs')
_ignore_para_names = [s.strip().lstrip(u'\\') for s in IgnoreParaStyles.split(u',') if s.strip()]

try:
    PrefixesToIgnore
except NameError:
    PrefixesToIgnore = ''
if not isinstance(PrefixesToIgnore, type(u'')):
    try:
        PrefixesToIgnore = PrefixesToIgnore.decode('utf-8')
    except UnicodeDecodeError:
        PrefixesToIgnore = PrefixesToIgnore.decode('mbcs')
try:
    SuffixesToIgnore
except NameError:
    SuffixesToIgnore = ''
if not isinstance(SuffixesToIgnore, type(u'')):
    try:
        SuffixesToIgnore = SuffixesToIgnore.decode('utf-8')
    except UnicodeDecodeError:
        SuffixesToIgnore = SuffixesToIgnore.decode('mbcs')

# Each space-separated token is either a plain affix (strip-only, unchanged
# from prior behavior) or a '/'-separated group of interchangeable variants
# (e.g. "ɨ/ʉ", "ión/iones", "i/ɨ/ʉ") for languages where a suffix triggers a
# stem-final alternation rather than simple concatenation.
def _parse_affix_groups(raw):
    groups = []
    for tok in raw.split():
        variants = [v.lower() for v in tok.split(u'/') if v]
        if variants:
            groups.append(variants)
    return groups

_prefix_groups = _parse_affix_groups(PrefixesToIgnore)
_suffix_groups = _parse_affix_groups(SuffixesToIgnore)

try:
    MidWordPunctuation
except NameError:
    MidWordPunctuation = '-'
if not isinstance(MidWordPunctuation, type(u'')):
    try:
        MidWordPunctuation = MidWordPunctuation.decode('utf-8')
    except UnicodeDecodeError:
        MidWordPunctuation = MidWordPunctuation.decode('mbcs')
_joiner_chars = MidWordPunctuation

try:
    SkipBeforeVerse
except NameError:
    SkipBeforeVerse = '['
if not isinstance(SkipBeforeVerse, type(u'')):
    try:
        SkipBeforeVerse = SkipBeforeVerse.decode('utf-8')
    except UnicodeDecodeError:
        SkipBeforeVerse = SkipBeforeVerse.decode('mbcs')
# Characters (e.g. the [ that opens a bracketed verse) that may stand just
# before the next \v; they are looked past when finding how a verse ends.
_skip_before_verse = u''.join(SkipBeforeVerse.split())

# Framework-injected (not a \optionName): current project name, used only for
# the "Project: X" line in the HTML report.
try:
    Project
except NameError:
    Project = ''
if not isinstance(Project, type(u'')):
    try:
        Project = Project.decode('utf-8')
    except UnicodeDecodeError:
        Project = Project.decode('mbcs')

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Strip \f...\f*, \x...\x*, \fig...\fig* spans from verse text so the true
# last/first character can be found.
INLINE_RE = re.compile(
    ur'\\f\s.*?\\f\*|\\x\s.*?\\x\*|\\fig\s.*?\\fig\*',
    re.UNICODE | re.DOTALL)

# Match whitespace + leading inline spans at the start of a verse's content.
# Used to skip \x, \f, \fig that precede the first real word.
LEADING_RE = re.compile(
    ur'^[\s\r\n]*(?:\\(?:f|x|fig)\b.*?\\(?:f\*|x\*|fig\*)\s*)*',
    re.UNICODE | re.DOTALL)

# Locate verse markers (\v N or \v N-M bridge).
VERSE_RE = re.compile(ur'\\v\s+\d+(?:-\d+)?\s*', re.UNICODE)

# Strip standalone and closing USFM character markers (\wj, \wj*, etc.) that
# appear within verse text so they don't appear as the last character.
USFM_MARKER_RE = re.compile(ur'\\[a-z][a-z0-9]*\*?', re.UNICODE)

# Gap allowed between consecutive words of a multi-word TermRenderings phrase:
# whitespace interleaved with USFM character markers (e.g. \wj Word\wj* Word2).
_PHRASE_GAP_RE = re.compile(
    ur'(?:[ \t\r\n]+|\\[a-z][a-z0-9]*\*?)*', re.UNICODE)

# Paragraph/structural markers (all three image lists: paragraph, poetry, list,
# section headings). When any of these appear in verse content it means there is
# a deliberate structural break before the next \v, so the capital check should
# be suppressed across that boundary.
PARA_BREAK_RE = re.compile(
    ur'\\(?:cls|pmo|pmc|pmr|pm|po|pr|pc|ph\d*|pi\d*|mi|nb|m|p|b'
    ur'|qac|qm\d*|qr|qc|qs|qa|qd|q\d*'
    ur'|lim\d*|litl|li\d*|lh|lf'
    ur'|s\d*|d|sp)\b',
    re.UNICODE)

# Prose-only structural markers for end-of-verse suppression.
# Excludes \b (blank line) and all \q* (poetry line markers): formatting-only,
# must not suppress cross-verse capital checking.
STRONG_BREAK_RE = re.compile(
    ur'\\(?:cls|pmo|pmc|pmr|pm|po|pr|pc|ph\d*|pi\d*|mi|nb|m|p'
    ur'|lim\d*|litl|li\d*|lh|lf'
    ur'|s\d*|d|sp)\b',
    re.UNICODE)

# Regex metacharacters in a TermRenderings word are matched literally: only the
# '*' at either end is a wildcard. Unescaped, a rendering such as '(a+)+b*' could
# freeze the check, and 'Sant[o*' stopped it with a pattern error. Non-ASCII
# letters are not backslashed (IronPython's .NET engine rejects such escapes).
def _re_literal(s):
    return re.sub(u'([\\\\.^$|?*+()\\[\\]{}])', u'\\\\\\1', s)

# Spans for user-specified character styles whose content is excluded from
# prev_end_char computation (e.g. \qs Selah\qs* in Psalms).
if _ignore_style_names:
    _style_pat = u'|'.join(
        u'\\\\' + _re_literal(s) + u'\\b.*?\\\\' + _re_literal(s) + u'\\*'
        for s in _ignore_style_names)
    IGNORE_STYLE_RE = re.compile(_style_pat, re.UNICODE | re.DOTALL)
else:
    IGNORE_STYLE_RE = None

# Paragraph marker + content up to the next USFM marker, excluded from
# prev_end_char computation (e.g. \sp Speaker, \r Cross-ref text).
if _ignore_para_names:
    _para_pat = u'|'.join(
        u'\\\\' + _re_literal(s) + u'\\b[^\\\\]*'
        for s in _ignore_para_names)
    IGNORE_PARA_RE = re.compile(_para_pat, re.UNICODE)
else:
    IGNORE_PARA_RE = None

# A "word char" is \w or a combining diacritical mark (U+0300-U+036F), so that
# words written with decomposed tone/accent marks (base letter + combining
# mark, e.g. o + combining grave = o-with-grave) are extracted whole instead
# of being truncated right before the mark.
_WORD_CHAR = u'(?:\\w|[\\u0300-\\u036f])'

def _build_word_pattern(joiners):
    if not joiners:
        return _WORD_CHAR + u'+'
    parts = []
    has_hyphen = u'-' in joiners
    for c in joiners:
        if c == u'-':
            continue
        parts.append(u'\\' + c if c in u'\\]^[' else c)
    cc = (u'-' if has_hyphen else u'') + u''.join(parts)
    return _WORD_CHAR + u'+(?:[' + cc + u']' + _WORD_CHAR + u'+)*'

_WORD_RE = re.compile(_build_word_pattern(_joiner_chars), re.UNICODE)

# ---------------------------------------------------------------------------
# Cross-chapter / cross-book state
# ---------------------------------------------------------------------------

_state = {
    'prev_end_char': None,
    'prev_book':     None,
    # Cleaned text of the previous verse (footnotes/xrefs/figures/ignored
    # styles/USFM markers removed), used only for the "words before" HTML
    # report context. Always set/cleared in lockstep with prev_end_char.
    'prev_context':  None,
}

# ---------------------------------------------------------------------------

def _base_char(s):
    # Skip trailing combining marks (Mn/Mc/Me) to find the base character a
    # verse actually ends with -- e.g. a vowel followed by a decomposed tone
    # mark should still be classified by the vowel's letter category, not the
    # mark's.
    i = len(s) - 1
    while i > 0 and unicodedata.category(s[i]) in (u'Mn', u'Mc', u'Me'):
        i -= 1
    return s[i]

def _is_recognized_root(root):
    root_nfc = unicodedata.normalize('NFC', root)
    root_lower = root_nfc.lower()
    if root_lower in _ignore_words_lower:
        return True
    if root_lower in _cap_single_word_exact_lower:
        return True
    if root_lower in _specific_case_lower:
        return True
    for spec in _cap_single_word_wildcards:
        if _spec_matches(spec, root_nfc):
            return True
    return False

def _word_has_affix(word_str):
    word_lower = word_str.lower()
    for group in _prefix_groups:
        for i, variant in enumerate(group):
            pl = len(variant)
            if len(word_str) <= pl or word_lower[:pl] != variant:
                continue
            if len(group) == 1:
                if _is_recognized_root(word_str[pl:]):
                    return True
            else:
                rest = word_str[pl:]
                for j, other in enumerate(group):
                    if j != i and _is_recognized_root(other + rest):
                        return True
    for group in _suffix_groups:
        for i, variant in enumerate(group):
            sl = len(variant)
            if len(word_str) <= sl or word_lower[-sl:] != variant:
                continue
            if len(group) == 1:
                if _is_recognized_root(word_str[:-sl]):
                    return True
            else:
                stem = word_str[:-sl]
                for j, other in enumerate(group):
                    if j != i and _is_recognized_root(stem + other):
                        return True
    return False

def _find_current_project_renderings():
    scr = getattr(checking, 'scr', None)
    if scr is None:
        return None
    d = getattr(scr, 'Directory', None)
    if not d:
        return None
    if isinstance(d, bytes):
        d = d.decode('mbcs')
    p = os.path.join(d, u'TermRenderings.xml')
    return p if os.path.isfile(p) else None

# A letter, combining marks included: Paratext runs these checks under IronPython,
# whose .NET \w covers the combining marks (Mn, U+0300-U+036F among them). The
# old form (?:[^\W\d_]|[\u0300-\u036f]) matched each mark both ways, so a word
# with many stacked marks made a failing wildcard match take exponential time.
_WORD_CHAR_NO_DIGIT = u'[^\\W\\d_]'

def _build_word_spec(word):
    has_prefix_wild = word.startswith(u'*')
    has_suffix_wild = word.endswith(u'*')
    root_word = word.strip(u'*')
    if not root_word:
        return None
    if has_prefix_wild or has_suffix_wild:
        prefix_pat = _WORD_CHAR_NO_DIGIT + u'*' if has_prefix_wild else u''
        suffix_pat = _WORD_CHAR_NO_DIGIT + u'*' if has_suffix_wild else u''
        return re.compile(
            u'\\A' + prefix_pat + _re_literal(root_word) + suffix_pat + u'\\Z',
            re.UNICODE)
    return root_word

def _load_cap_renderings(path):
    phrases = []
    open_path = path.encode('mbcs') if isinstance(path, type(u'')) else path
    with open(open_path, 'rb') as f:
        data = f.read()
    root = ET.fromstring(data)
    for tr in root.iter(u'TermRendering'):
        r_elem = tr.find(u'Renderings')
        if r_elem is None or not r_elem.text:
            continue
        for token in r_elem.text.split(u'||'):
            at = token.find(u'@')
            if at >= 0:
                token = token[:at]
            words = token.split()
            if not words:
                continue
            first_root = words[0].strip(u'*')
            if not first_root or unicodedata.category(first_root[0]) != u'Lu':
                continue
            specs = []
            for word in words:
                spec = _build_word_spec(word)
                if spec is None:
                    specs = None
                    break
                specs.append(spec)
            if specs:
                phrases.append(specs)
    return phrases

# Words SpellingStatus.xml marks as always written with a given case
# (<Status Word="galilaaya"><SpecificCase>Galilaaya</SpecificCase>). Only the
# forms that start with a capital matter here.
def _load_specific_case(path):
    exact = set()
    open_path = path.encode('mbcs') if isinstance(path, type(u'')) else path
    with open(open_path, 'rb') as f:
        data = f.read()
    root = ET.fromstring(data)
    for sc in root.iter(u'SpecificCase'):
        word = (sc.text or u'').strip()
        if not word:
            continue
        if not isinstance(word, type(u'')):
            word = word.decode('utf-8')
        word = unicodedata.normalize('NFC', word)
        if unicodedata.category(word[0]) == u'Lu':
            exact.add(word)
    return frozenset(exact), frozenset(w.lower() for w in exact)

# Optional names dictionary: a Toolbox/SFM dictionary (.dic) whose capitalized
# names are treated like capitalized Biblical Terms renderings. Off unless the
# user fills in NamesDictionaryFile. Every line that starts with one of the
# chosen markers (e.g. lx, a) supplies one name: the first word of its value,
# without a leading "+" and without any "/ environment" or "| comment" after
# it. A word followed by a "+" (a morpheme break) is skipped. Only names that
# start with a capital letter can matter to this check, so the rest are dropped.
_DIC_MARKER_OK_RE = re.compile(ur'^[A-Za-z0-9_]{1,32}$', re.UNICODE)
_DIC_BAD_PATH_CHARS = u'<>"|*?\x00\r\n\t'

# Returns the list of marker names (no backslash) from a comma-separated
# option value: ['lx'] if it is empty, or None if any entry holds anything but
# letters, digits and underscores (so no entry can ever alter the regex it is
# built into) or there are more than 20. A leading backslash is tolerated, as
# in IgnoreStyles.
def _clean_dic_markers(raw):
    markers = []
    for token in raw.split(u','):
        marker = token.strip().lstrip(u'\\').strip()
        if not marker:
            continue
        if not _DIC_MARKER_OK_RE.match(marker):
            return None
        if marker not in markers:
            markers.append(marker)
    if len(markers) > 20:
        return None
    return markers or [u'lx']

# Returns the path without surrounding spaces/quotes (Explorer's "Copy as
# path" adds quotes), or None if it is empty or has characters that cannot be
# in a Windows path.
def _clean_dic_path(raw):
    path = raw.strip().strip(u'"').strip()
    if not path or any(c in path for c in _DIC_BAD_PATH_CHARS):
        return None
    return path

def _load_dic_names(path, markers):
    with open(_open_path(path), 'rb') as f:
        data = f.read()
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('mbcs')
    line_re = re.compile(
        u'^\\\\(?:' + u'|'.join(markers) + ur')\s+\+?([^\s/|]+)(?=\s|/|\||$)(?!\s*\+)',
        re.UNICODE)
    names = set()
    for line in text.lstrip(u'\ufeff').splitlines():
        m = line_re.match(line)
        if not m:
            continue
        word = unicodedata.normalize('NFC', m.group(1))
        if unicodedata.category(word[0]) == u'Lu':
            names.add(word)
    return [[w] for w in sorted(names)]

def _spec_matches(spec, word):
    if isinstance(spec, type(u'')):
        return word == spec
    return bool(spec.match(word))

def _extract_word_seq(text, start, max_words):
    words = []
    pos = start
    for i in range(max_words):
        if i > 0:
            gap_m = _PHRASE_GAP_RE.match(text, pos)
            new_pos = gap_m.end() if gap_m else pos
            if new_pos == pos:
                break
            pos = new_pos
        m = _WORD_RE.match(text, pos)
        if not m:
            break
        words.append(text[pos:m.end()])
        pos = m.end()
    return words

def _index_cap_phrases(phrases):
    by_first_word = {}
    wildcard_first = []
    for phrase in phrases:
        first = phrase[0]
        if isinstance(first, type(u'')):
            by_first_word.setdefault(first, []).append(phrase)
        else:
            wildcard_first.append(phrase)
    return by_first_word, wildcard_first

def _index_single_word_terms(phrases):
    exact_lower = set()
    wildcards = []
    for phrase in phrases:
        if len(phrase) != 1:
            continue
        spec = phrase[0]
        if isinstance(spec, type(u'')):
            exact_lower.add(spec.lower())
        else:
            wildcards.append(spec)
    return frozenset(exact_lower), wildcards

def _phrase_matches_at(text, start, phrase):
    words = _extract_word_seq(text, start, len(phrase))
    if len(words) != len(phrase):
        return False
    return all(_spec_matches(spec, words[i]) for i, spec in enumerate(phrase))

def _match_cap_phrase(text, start):
    m = _WORD_RE.match(text, start)
    if not m:
        return False
    first_word = text[start:m.end()]
    for phrase in _cap_phrases_by_first_word.get(first_word, ()):
        if len(phrase) == 1 or _phrase_matches_at(text, start, phrase):
            return True
    for phrase in _cap_phrases_wildcard_first:
        if _phrase_matches_at(text, start, phrase):
            return True
    return False

def _is_ignored_at(verse_text, pos, word_str):
    if _match_cap_phrase(verse_text, pos):
        return True
    word_nfc = unicodedata.normalize('NFC', word_str)
    if word_nfc in _ignore_words or word_nfc in _specific_case_words:
        return True
    if _dic_allow_suffixes and _starts_with_dic_name(word_nfc):
        return True
    return _word_has_affix(word_str)

# Optional (NamesDictionaryAllowSuffixes): for languages whose suffix
# combinations can't be listed, any word that begins with a dictionary name
# (case-sensitive, name followed by anything) counts as that name.
def _starts_with_dic_name(word_nfc):
    for i in range(1, len(word_nfc) + 1):
        if word_nfc[:i] in _dic_names:
            return True
    return False

# ---------------------------------------------------------------------------
# HTML report support
# ---------------------------------------------------------------------------

def _he(s):
    return s.replace(u'&', u'&amp;').replace(u'<', u'&lt;').replace(u'>', u'&gt;')

def _to_utf8_bytes(s):
    # A project directory path is not guaranteed to be ASCII (e.g. an
    # accented project/folder name); sys.stdout.write on a unicode string
    # containing non-ASCII characters shows as a replacement character in
    # Paratext's info panel unless encoded explicitly first.
    if isinstance(s, type(u'')):
        return s.encode('utf-8')
    return s

_WS_RUN_RE = re.compile(ur'[ \t]+', re.UNICODE)
_SPACE_BEFORE_PUNCT_RE = re.compile(ur' +([,;.:!?])', re.UNICODE)

def _collapse_ws(s):
    return _WS_RUN_RE.sub(u' ', s.replace(u'\r', u'').replace(u'\n', u' '))

def _clean_for_display(s):
    # Same exclusions as the prev_end_char pipeline below (INLINE_RE, then
    # IgnoreStyles/IgnoreParaStyles if configured, then any remaining bare
    # USFM marker), so the report context matches what the check itself
    # evaluated -- but spans are replaced with a space rather than deleted,
    # so a footnote/xref/figure sitting directly between two words doesn't
    # glue them together.
    s = INLINE_RE.sub(u' ', s)
    if IGNORE_STYLE_RE:
        s = IGNORE_STYLE_RE.sub(u' ', s)
    if IGNORE_PARA_RE:
        s = IGNORE_PARA_RE.sub(u' ', s)
    s = USFM_MARKER_RE.sub(u' ', s)
    s = _collapse_ws(s).strip()
    # A removed note/xref/figure directly before punctuation leaves a
    # stray space (e.g. "word \f...\f*," -> "word ,") -- purely cosmetic,
    # so tighten it back up for display.
    return _SPACE_BEFORE_PUNCT_RE.sub(ur'\1', s)

def _last_n_words(text, n):
    if not text:
        return u''
    matches = list(_WORD_RE.finditer(text))
    if not matches:
        return text.strip()
    start = matches[-n].start() if len(matches) >= n else 0
    return text[start:].strip()

def _after_context_html(text, n):
    matches = []
    for m in _WORD_RE.finditer(text):
        matches.append(m)
        if len(matches) >= n:
            break
    if not matches:
        return _he(text.strip())
    end = matches[-1].end()
    snippet = text[:end]
    lead = len(snippet) - len(snippet.lstrip())
    snippet = snippet.lstrip()
    fs, fe = matches[0].start() - lead, matches[0].end() - lead
    return u'{0}<span class="err">{1}</span>{2}'.format(
        _he(snippet[:fs]), _he(snippet[fs:fe]), _he(snippet[fe:]))

def _project_directory():
    scr = getattr(checking, 'scr', None)
    d = getattr(scr, 'Directory', None) if scr is not None else None
    if not d:
        return None
    if isinstance(d, bytes):
        d = d.decode('mbcs')
    return d

def _open_path(path):
    return path.encode('mbcs') if isinstance(path, type(u'')) else path

def _log_crash(label, exc):
    directory = _directory if '_directory' in globals() else None
    directory = directory or os.environ.get('TEMP') or os.environ.get('TMP')
    if not directory:
        return
    try:
        tb_text = traceback.format_exc()
        if isinstance(tb_text, str):
            tb_text = tb_text.decode('utf-8', 'replace')
    except Exception:
        try:
            tb_text = unicode(repr(exc))
        except Exception:
            tb_text = u'<unformattable exception>'
    log_path = os.path.join(directory, u'CapitalAtVerseDebug.log')
    try:
        with open(_open_path(log_path), 'ab') as f:
            f.write(u'--- {0} ---\n'.format(label).encode('utf-8'))
            f.write(tb_text.encode('utf-8', 'replace'))
            f.write(u'\n'.encode('utf-8'))
    except Exception:
        pass

_report_rows = []  # dicts: ref, goto, verse_num, before, after_html

def write_html_report(html_path, project_name, rows):
    lines = []
    lines.append(u'<!DOCTYPE html>')
    lines.append(u'<html><head><meta charset="utf-8">')
    lines.append(u'<title>Rapport des majuscules en début de verset</title>')
    lines.append(u'<style>')
    lines.append(u'body{font-family:sans-serif;font-size:13px}')
    lines.append(u'table{border-collapse:collapse;margin-bottom:12px}')
    lines.append(u'th,td{border:1px solid #bbb;padding:3px 8px;vertical-align:top}')
    lines.append(u'th{background:#ddd}')
    lines.append(u'.err{color:#c00;font-weight:bold}')
    lines.append(u'.vn{color:#666;font-weight:bold}')
    lines.append(u'</style></head><body>')
    lines.append(u'<h1>Rapport des majuscules en début de verset</h1>')
    if project_name:
        lines.append(u'<p>Projet : <b>{0}</b></p>'.format(_he(project_name)))
    lines.append(u'<p>{0} cas signalé(s).</p>'.format(len(rows)))
    if rows and _links_on:
        lines.append(_ptx_goto.hint_html('fr'))

    if not rows:
        lines.append(u'<p><i>Aucun problème trouvé.</i></p>')
    else:
        lines.append(u'<table><tr><th>Référence</th><th>Contexte</th></tr>')
        for row in rows:
            context = u'{0} <sup class="vn">{1}</sup> {2}'.format(
                _he(row['before']), _he(row['verse_num']), row['after_html'])
            lines.append(u'<tr><td><b>{0}</b></td><td>{1}</td></tr>'.format(
                _ref_link(_he(row['ref']), row.get('goto')), context))
        lines.append(u'</table>')

    lines.append(u'</body></html>')
    html = u'\n'.join(lines)
    with open(_open_path(html_path), 'wb') as f:
        f.write(html.encode('utf-8'))

# ---------------------------------------------------------------------------
checking.setupCheck()
# ---------------------------------------------------------------------------

_tr_path = _find_current_project_renderings() if _ignore_bt else None
_cap_phrases = _load_cap_renderings(_tr_path) if _tr_path else []

_dic_names = frozenset()
if NamesDictionaryFile.strip():
    _dic_path = _clean_dic_path(NamesDictionaryFile)
    _dic_markers = _clean_dic_markers(NamesDictionaryMarkers)
    if _dic_markers is None:
        _sys.stdout.write(_to_utf8_bytes(
            u'# Dictionnaire de noms ignore : les marqueurs "{0}" sont invalides (indiquez '
            u'des noms de marqueurs sans barre oblique inverse, separes par des '
            u'virgules, avec seulement des lettres, chiffres et traits de '
            u'soulignement, p. ex. lx, a ; 20 au maximum).\n'.format(
                NamesDictionaryMarkers.strip())))
    elif _dic_path is None or not os.path.isfile(_open_path(_dic_path)):
        _sys.stdout.write(_to_utf8_bytes(
            u'# Dictionnaire de noms ignore : fichier introuvable : {0}\n'.format(
                NamesDictionaryFile.strip())))
    else:
        try:
            _dic_phrases = _load_dic_names(_dic_path, _dic_markers)
            _dic_names = frozenset(p[0] for p in _dic_phrases)
            _cap_phrases.extend(_dic_phrases)
            _sys.stdout.write(_to_utf8_bytes(
                u'# Dictionnaire de noms : {0} nom(s) avec majuscule lu(s) dans les lignes {1} '
                u'de {2}\n'.format(
                    len(_dic_phrases),
                    u', '.join(u'\\' + m for m in _dic_markers), _dic_path)))
        except Exception as e:
            _log_crash(u'names dictionary', e)
            _sys.stdout.write(_to_utf8_bytes(
                u'# Dictionnaire de noms ignore : lecture impossible ; voir '
                u'CapitalAtVerseDebug.log\n'))
_cap_phrases_by_first_word, _cap_phrases_wildcard_first = _index_cap_phrases(_cap_phrases)
_cap_single_word_exact_lower, _cap_single_word_wildcards = _index_single_word_terms(_cap_phrases)

_directory = _project_directory()

_specific_case_words, _specific_case_lower = frozenset(), frozenset()
if _ignore_wordlist and _directory:
    _ss_path = os.path.join(_directory, u'SpellingStatus.xml')
    if os.path.isfile(_open_path(_ss_path)):
        try:
            _specific_case_words, _specific_case_lower = _load_specific_case(_ss_path)
        except Exception as e:
            _log_crash(u'SpellingStatus.xml', e)

_links_on = _ptx_goto is not None and _ptx_goto.enabled(_directory)

class _StripCRLF(object):
    def __init__(self, wrapped):
        self._w = wrapped
        self.last_ref = None
    def write(self, s):
        if '\t\t' in s and not s.startswith('#'):
            try:
                ref, rest = s.split('\t\t', 1)
                text, msg = rest.rsplit('\t', 1)
                text = re.sub(r'^\[\d+\]', '', text)
                text = text.replace('\\u000d', '').replace('\\u000a', ' ')
                self.last_ref = ref
                self._w.write(ref + '\t\t' + text + '\t' + msg)
                return
            except ValueError:
                pass
        self._w.write(s)
    def flush(self):
        self._w.flush()
    def close(self):
        self._w.close()

_sys.stdout = _StripCRLF(_sys.stdout)

# ---------------------------------------------------------------------------

def _checkChapter_impl(reference, text, lastChapter):
    # reference is a VerseRefPy object; .Book is an integer book number.
    book = reference.Book if reference else None

    # Reset state at every new book.
    if book != _state['prev_book']:
        _state['prev_end_char'] = None
        _state['prev_context'] = None
        _state['prev_book'] = book

    verse_matches = list(VERSE_RE.finditer(text))
    if not verse_matches:
        return

    # If structural markers appear before the first \v (e.g. \d, \s1, \q1),
    # they represent a section/paragraph break -- suppress any carry-over check.
    if PARA_BREAK_RE.search(text[:verse_matches[0].start()]):
        _state['prev_end_char'] = None
        _state['prev_context'] = None

    for idx, vm in enumerate(verse_matches):
        content_start = vm.end()
        if idx + 1 < len(verse_matches):
            content_end = verse_matches[idx + 1].start()
        else:
            content_end = len(text)
        verse_text = text[content_start:content_end]

        # ---- Check this verse's START against the previous verse's END ----
        prev = _state['prev_end_char']
        if prev and prev not in _final_set:
            m    = LEADING_RE.match(verse_text)
            skip = m.end() if m else 0
            while skip < len(verse_text) and verse_text[skip] in ' \t\r\n':
                skip += 1
            _skipped_quote = False
            while skip < len(verse_text):
                c = verse_text[skip]
                _is_opener = (c in _quote_openers) if _quote_openers is not None else (unicodedata.category(c) in (u'Pi', u'Pf'))
                if _is_opener:
                    _skipped_quote = True
                    skip += 1
                    while skip < len(verse_text) and verse_text[skip] in u' \t\r\n':
                        skip += 1
                else:
                    break
            if skip < len(verse_text):
                first_char = verse_text[skip]
                if unicodedata.category(first_char) == 'Lu' and not (_ignore_cap_after_quote and _skipped_quote):
                    m_next = _WORD_RE.match(verse_text, skip)
                    word_str = verse_text[skip:m_next.end()] if m_next else u''
                    if not _is_ignored_at(verse_text, skip, word_str):
                        span_start = content_start + skip
                        if m_next:
                            span_end = content_start + m_next.end()
                        else:
                            span_end = content_start + skip + 1
                        checking.outputError(span_start, span_end, '')

                        verse_num_m = re.search(ur'\d+(?:-\d+)?', vm.group(0), re.UNICODE)
                        ref = getattr(_sys.stdout, 'last_ref', None) or u'?'
                        if isinstance(ref, bytes):
                            ref = ref.decode('utf-8', 'replace')
                        _report_rows.append({
                            'ref': ref,
                            'goto': _goto(ref),
                            'verse_num': verse_num_m.group(0) if verse_num_m else u'?',
                            'before': _last_n_words(_state.get('prev_context'), 3),
                            'after_html': _after_context_html(_clean_for_display(verse_text), 3),
                        })

        # ---- Compute END character of this verse ----
        # Suppress the check across this boundary only when a structural
        # paragraph marker is TRAILING -- i.e. no real text follows it before
        # the next \v.  A mid-verse marker like \li1 is not trailing and must
        # not suppress the check.  Text of IgnoreParaStyles markers (e.g. the
        # speaker label of a trailing \sp) and SkipBeforeVerse characters
        # (e.g. "\p [") don't count as real text.
        suppress = False
        last_break = None
        for mb in STRONG_BREAK_RE.finditer(verse_text):
            last_break = mb
        if last_break is not None:
            tail = verse_text[last_break.start():]
            if IGNORE_PARA_RE:
                tail = IGNORE_PARA_RE.sub(u'', tail)
            tail = USFM_MARKER_RE.sub(u'', tail)
            tail = tail.rstrip(u' \t\r\n' + _skip_before_verse).strip()
            is_section = re.match(ur'^\\(?:s\d*|d)\b', last_break.group(0), re.UNICODE)
            if is_section or not tail:
                suppress = True

        if suppress:
            _state['prev_end_char'] = None
            _state['prev_context'] = None
        else:
            stripped = INLINE_RE.sub(u'', verse_text)
            if IGNORE_STYLE_RE:
                stripped = IGNORE_STYLE_RE.sub(u'', stripped)
            if IGNORE_PARA_RE:
                stripped = IGNORE_PARA_RE.sub(u'', stripped)
            stripped = USFM_MARKER_RE.sub(u'', stripped).rstrip()
            # Peel trailing quotation marks (Pi/Pf categories + ASCII quotes)
            # and closing brackets (Pe) so that e.g. a verse ending in ,"
            # is treated as ending with , and one ending in .) with .
            # SkipBeforeVerse characters are peeled too, so "word. [" ends
            # with .
            while stripped:
                c = stripped[-1]
                cat = unicodedata.category(c)
                if cat in ('Pi', 'Pf', 'Pe') or c in ('"', "'") or c in _skip_before_verse:
                    stripped = stripped[:-1].rstrip()
                else:
                    break
            _state['prev_end_char'] = _base_char(stripped) if stripped else None
            _state['prev_context'] = _clean_for_display(verse_text)

def checkChapter(reference, text, lastChapter):
    try:
        _checkChapter_impl(reference, text, lastChapter)
    except Exception as e:
        _log_crash(u'checkChapter', e)

checking.checkAllChapters(checkChapter)

if _directory:
    _html_path = os.path.join(_directory, u'RapportMajusculeDebutVerset.html')
    try:
        write_html_report(_html_path, Project, _report_rows)
        os.startfile(_open_path(_html_path))
        _sys.stdout.write(_to_utf8_bytes(u'# Rapport ecrit dans {0}\n'.format(_html_path)))
    except Exception as e:
        _log_crash(u'write_html_report', e)
        _sys.stdout.write(_to_utf8_bytes(u'# Erreur pendant l\'ecriture du rapport HTML ; voir CapitalAtVerseDebug.log\n'))
else:
    _sys.stdout.write(_to_utf8_bytes(u'# Erreur : impossible de determiner le dossier du projet ; aucun rapport ecrit.\n'))
