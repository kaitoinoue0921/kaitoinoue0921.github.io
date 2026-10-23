"""項目タイトルの $...$（TeX）を、<title> や一覧で読める文字に崩す。"""
import re

SUP = str.maketrans('0123456789+-=()nixyabzkmtcde', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣʸᵃᵇᶻᵏᵐᵗᶜᵈᵉ')
SUB = str.maketrans('0123456789+-=()aeoxhklmnpstijruv', '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₕₖₗₘₙₚₛₜᵢⱼᵣᵤᵥ')
GREEK = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'Delta': 'Δ', 'theta': 'θ', 'lambda': 'λ',
         'mu': 'μ', 'pi': 'π', 'rho': 'ρ', 'sigma': 'σ', 'omega': 'ω', 'Omega': 'Ω', 'phi': 'φ', 'varepsilon': 'ε',
         'epsilon': 'ε', 'infty': '∞', 'times': '×', 'cdot': '・', 'to': '→', 'rightarrow': '→', 'leqq': '≦',
         'geqq': '≧', 'leq': '≦', 'geq': '≧', 'le': '≦', 'ge': '≧', 'neq': '≠', 'ne': '≠', 'pm': '±', 'int': '∫',
         'sum': 'Σ', 'cdots': '…', 'ldots': '…', 'circ': '°', 'degree': '°', 'perp': '⊥', 'parallel': '∥',
         'angle': '∠', 'triangle': '△', 'equiv': '≡', 'approx': '≒', 'fallingdotseq': '≒', 'quad': ' ',
         'left': '', 'right': '', 'displaystyle': '', ',': ' ', ';': ' ', '!': ''}


def _script(arg, table):
    out = arg.translate(table)
    if all(c != o or not c.isalnum() for c, o in zip(out, arg)):
        return out
    # 上付き・下付きの文字がないとき: 上付きは ^ をつけて、下付きは素の文字で
    if len(arg) > 1 and not (arg[0] == '(' and arg[-1] == ')'):
        arg = '(' + arg + ')'
    return '^' + arg if table is SUP else arg


def _wrap(x):
    return '(' + x + ')' if re.search(r'[+\-=,\s]', x) else x


def _ce(m):
    t = m.group(1)
    t = re.sub(r'\^\{?([0-9]*[+-])\}?', lambda x: x.group(1).translate(SUP), t)   # Fe^2+ → Fe²⁺
    t = re.sub(r'(?<=[A-Za-z)\]])(\d+)', lambda x: x.group(1).translate(SUB), t)  # H2O → H₂O
    return t


def tex_plain(t):
    t = re.sub(r'\\ce\{((?:[^{}]|\{[^{}]*\})*)\}', _ce, t)
    t = t.replace('\\ ', ' ')
    t = re.sub(r'\\(?:bar|overline)\s*(?:\{([^{}]*)\}|([A-Za-z]))', lambda m: (m.group(1) or m.group(2)) + '\u0304', t)
    t = re.sub(r'\\d?frac\s*([0-9A-Za-z])\s*([0-9A-Za-z])', r'\1/\2', t)
    t = re.sub(r'\\(?:mathrm|text|mathbf|operatorname|vec|overrightarrow|overline|bm|boldsymbol)\{([^{}]*)\}', r'\1', t)
    for _ in range(2):
        t = re.sub(r'\\d?frac\{([^{}]*)\}\{([^{}]*)\}', lambda m: _wrap(m.group(1)) + '/' + _wrap(m.group(2)), t)
        t = re.sub(r'\\sqrt\{([^{}]*)\}', lambda m: '√' + (m.group(1) if len(m.group(1)) == 1 else '(' + m.group(1) + ')'), t)
    t = re.sub(r'\\sqrt\s*([0-9a-z])', r'√\1', t)
    t = re.sub(r'\\([A-Za-z]+|[,;!])', lambda m: GREEK.get(m.group(1), m.group(1) if m.group(1) in
                                                          ('sin', 'cos', 'tan', 'log', 'lim', 'max', 'min', 'gcd', 'lcm', 'exp') else ''), t)
    # 1回の置換で処理する（崩した結果の ^ をもう一度拾わないように）
    t = re.sub(r'\^(?:\{([^{}]*)\}|(\([^()]*\))|(\S))', lambda m: _script(next(g for g in m.groups() if g is not None), SUP), t)
    t = re.sub(r'_(?:\{([^{}]*)\}|(\S))', lambda m: _script(next(g for g in m.groups() if g is not None), SUB), t)
    return t.replace('{', '').replace('}', '')


def title_plain(title):
    """'$a^3+b^3$ の因数分解' → 'a³+b³ の因数分解'"""
    return re.sub(r'\$([^$]+)\$', lambda m: tex_plain(m.group(1)), title).strip()
