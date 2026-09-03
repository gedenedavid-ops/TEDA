"""
Generate a comprehensive PDF report of the project for the trader.
Includes: cover, accomplishments, strategy, architecture, decisions, test results.
"""

from pathlib import Path
from fpdf import FPDF

# Path to Windows system fonts that support Unicode (French accents, etc.)
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_ITALIC = "C:/Windows/Fonts/ariali.ttf"
FONT_MONO = "C:/Windows/Fonts/cour.ttf"


class Report(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, "TEDA — Rapport Hackathon", align="L")
            self.cell(0, 5, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(3)

    def footer(self):
        pass

    def title_block(self, text, level=1):
        sizes = {1: 16, 2: 13, 3: 11}
        self.set_font("Arial", "B", sizes.get(level, 10))
        self.set_text_color(20, 60, 120)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=5):
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.cell(indent, 5.5, "")
        self.set_font("Arial", "", 10)
        self.cell(4, 5.5, chr(8226))
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 8)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(50, 50, 50)
        for line in text.split("\n"):
            self.cell(0, 4.5, "  " + line, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def success_badge(self, text):
        self.set_font("Arial", "B", 10)
        self.set_text_color(0, 140, 60)
        self.cell(0, 5.5, "  " + text, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 30, 30)
        self.ln(1)

    def section_line(self):
        self.set_draw_color(20, 60, 120)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)


def build_report():
    pdf = Report()
    pdf.set_auto_page_break(True, 15)

    # Register Unicode fonts for French text.
    pdf.add_font("Arial", "", FONT_REGULAR, uni=True)
    pdf.add_font("Arial", "B", FONT_BOLD, uni=True)
    pdf.add_font("Arial", "I", FONT_ITALIC, uni=True)
    pdf.add_font("Courier", "", FONT_MONO, uni=True)

    pdf.add_page()

    # ---- COVER ------------------------------------------------------------
    pdf.ln(30)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 12, "TEDA", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Hackathon lablab.ai x Alpaca", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, "Agent de trading autonome base sur la strategie SMV", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Rapport de la journee du 31 aout 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_draw_color(20, 60, 120)
    pdf.set_line_width(0.6)
    pdf.line(50, pdf.get_y(), 160, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Equipe: GEDENE-OPS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Stack: Python + Alpaca SDK + Featherless AI + CLI", align="C", new_x="LMARGIN", new_y="NEXT")

    # ---- RESUME EXECUTIF -------------------------------------------------
    pdf.add_page()
    pdf.title_block("Resume executif")
    pdf.section_line()
    pdf.body(
        "Ce rapport presente l'ensemble des travaux realises le 31 aout 2026 "
        "dans le cadre du hackathon lablab.ai x Alpaca. L'objectif est de "
        "construire un agent de trading autonome (TEDA) utilisant l'API Alpaca, le "
        "CLI Alpaca, et un LLM open-source via Featherless AI pour generer du "
        "P&L en paper trading avec des options."
    )
    pdf.body(
        "La strategie retenue est la SMV (Smart Money Vision), une approche "
        "SMC/ICT adaptee du marche Forex au marche des options actions. "
        "L'agent a ete entierement code et teste en conditions reelles sur "
        "les donnees Alpaca paper, avec un premier signal BUY detecte sur QQQ "
        "(RR 12.5, tous les filtres valides)."
    )

    # ---- ACCOMPLISSEMENTS ------------------------------------------------
    pdf.title_block("Ce qui a ete accompli aujourd'hui")
    pdf.section_line()
    pdf.body("En une journee, l'infrastructure complete a ete construite et validee de bout en bout :")
    pdf.ln(2)

    accomplishments = [
        "Analyse du PDF 44 pages du trader (strategie SMV) et adaptation au marche options",
        "Connexion au compte Alpaca paper ($100,000, options niveau 3)",
        "Implementation des 5 modules de detection SMV (structure, zones OB, imbalance, liquidite, triggers)",
        "Chaine de 5 filtres validee a 100% par le trader",
        "Regle de sweep integree (zone clean vs inducement)",
        "Recuperation de donnees reelles SPY/QQQ/AAPL (flux IEX)",
        "Integration Featherless LLM (Qwen/Qwen2.5-7B-Instruct) pour le raisonnement",
        "Boucle autonome fonctionnelle (analyse -> signal -> journalisation)",
        "Premier signal BUY detecte sur QQQ (RR 12.5, tous les filtres OK)",
        "Journal des decisions + documentation complete (strategie, architecture, decisions)",
    ]
    for a in accomplishments:
        pdf.success_badge(a)

    # ---- STRATEGIE -------------------------------------------------------
    pdf.add_page()
    pdf.title_block("Strategie SMV (Smart Money Vision)")
    pdf.section_line()
    pdf.body(
        "La SMV est une strategie basee sur les mouvements des 'big boys' "
        "(institutions). Elle repose sur 4 piliers : Structure, Offre & Demande, "
        "Cause & Effet, et Liquidite."
    )
    pdf.title_block("Regles d'or", level=2)
    pdf.bullet("Risque maximum : 1% par trade")
    pdf.bullet("Risk/Reward minimum : 1:7")
    pdf.bullet("Stop Loss : serre (zone invalidee)")
    pdf.title_block("Les 4 piliers", level=2)
    pdf.bullet("Structure (la reine) : biais directionnel 80% impulsion / 20% retracement")
    pdf.bullet("Offre & Demande : zones OB (bougie manipulatrice + bougie qui prend l'argent)")
    pdf.bullet("Cause & Effet : accumulation/distribution, Wyckoff Phases A->E")
    pdf.bullet("Liquidite : EQL/EQH, signatures, inducement, sweep")
    pdf.title_block("Chaine d'entree (5 filtres)", level=2)
    pdf.body(
        "Structure HTF (biais 80%) -> Zone OB -> Imbalance (confirme) -> "
        "Liquidite (sweep) -> Market Shift LTF -> ENTREE"
    )
    pdf.title_block("Regle du sweep (cle)", level=2)
    pdf.bullet("Zone 'clean' : liquidite externe deja sweepee -> zone PRIORITAIRE (piege purge)")
    pdf.bullet("Zone 'inducement' : liquidite encore devant -> PIEGE, a eviter")
    pdf.title_block("Mapping Forex -> Options", level=2)
    pdf.bullet("Structure bullish -> Buy Call / Call debit spread / Sell Put")
    pdf.bullet("Structure bearish -> Buy Put / Put debit spread / Sell Call")
    pdf.bullet("Consolidation / Wyckoff B -> Iron Condor / Short Strangle (theta)")
    pdf.title_block("Timeframes", level=2)
    pdf.bullet("Structure + 80/20 : D1 / H4")
    pdf.bullet("Zones OB / POI : H4 / H1")
    pdf.bullet("Imbalance + Liquidite + Market Shift : H1 / M15")

    # ---- ARCHITECTURE ----------------------------------------------------
    pdf.add_page()
    pdf.title_block("Architecture technique")
    pdf.section_line()
    pdf.title_block("Stack", level=2)
    pdf.bullet("Python 3.14 + alpaca-py (SDK officiel)")
    pdf.bullet("Featherless AI (LLM open-source, endpoint compatible OpenAI)")
    pdf.bullet("Alpaca CLI (exigence du hackathon)")
    pdf.bullet("pandas / numpy pour le calcul technique")
    pdf.title_block("Modules", level=2)
    modules = [
        "strategy/structure.py     - biais 80/20, BOS, swing points",
        "strategy/supply_demand.py - zones OB + breaker blocks",
        "strategy/imbalance.py     - FVG / IPA (confirme les zones)",
        "strategy/liquidity.py    - EQL/EQH + sweep (tri des zones)",
        "strategy/triggers.py     - chaine 5 filtres -> BUY/SELL/NONE",
        "data/market_data.py      - OHLCV Alpaca -> DataFrame",
        "execution/client.py      - wrapper TradingClient",
        "execution/options.py     - signal -> contrat option ATM",
        "agent/main.py            - boucle autonome",
        "agent/decision.py        - raisonnement LLM + journalisation",
        "agent/risk.py            - sizing 1% / RR 1:7",
    ]
    for m in modules:
        pdf.bullet(m, indent=8)
    pdf.title_block("Flux de donnees", level=2)
    pdf.code_block(
        "Alpaca Paper (IEX)\n"
        "  | fetch_stock_bars(symbol, timeframe)\n"
        "  v\n"
        "DataFrame OHLCV\n"
        "  |\n"
        "  +-- HTF (1D)  -> structure -> biais 80/20\n"
        "  +-- H4/H1     -> zones OB\n"
        "  +-- H1/M15    -> imbalance + liquidite\n"
        "  +-- triggers -> Signal (BUY/SELL/NONE)\n"
        "  |\n"
        "  v\n"
        "Risk check -> LLM reasoning -> Journal -> [ordre paper]"
    )

    # ---- DECISIONS -------------------------------------------------------
    pdf.add_page()
    pdf.title_block("Journal des decisions")
    pdf.section_line()
    pdf.body(
        "Chaque decision technique et strategique a ete consignee et datee. "
        "Voici les decisions principales prises aujourd'hui :"
    )
    decisions = [
        ("D01 - Stack", "Python + Alpaca Python SDK + CLI (pas MCP)"),
        ("D02 - IA", "Featherless (open-source) via Qwen/Qwen2.5-7B-Instruct"),
        ("D03 - Strategie", "SMV adaptee du PDF 44 pages du trader"),
        ("D04 - Timeframes", "D1/H4 (structure), H4/H1 (zones), H1/M15 (triggers)"),
        ("D05 - 5 filtres", "Biais HTF -> Zone OB -> Imbalance -> Liquidite -> Market Shift"),
        ("D06 - Sweep", "Zone clean (sweeped) = prioritaire, inducement = piege"),
        ("D07 - Flux", "IEX gratuit (15j intraday) accepte pour le dev"),
        ("D08 - Compte", "Paper $100,000, options niveau 3 (calls, puts, spreads)"),
        ("D09 - Risque", "1% max/trade, RR min 1:7, position max 25%"),
    ]
    for label, desc in decisions:
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(20, 60, 120)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 6, "  " + desc, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ---- RESULTATS LIVE --------------------------------------------------
    pdf.add_page()
    pdf.title_block("Test en conditions reelles")
    pdf.section_line()
    pdf.body(
        "La boucle autonome a ete executee le 31/08/2026 sur les donnees "
        "reelles Alpaca paper. Voici les resultats complets :"
    )
    pdf.title_block("Resultats par symbole", level=2)
    pdf.code_block(
        "SPY @ 765.55  -> biais BULLISH  -> NONE (liquidite = inducement)\n"
        "QQQ @ 714.49  -> biais BULLISH  -> BUY  (tous les filtres OK)\n"
        "AAPL @ 313.40 -> biais NEUTRAL  -> NONE (pas de biais clair)"
    )
    pdf.title_block("Signal BUY QQQ - detail", level=2)
    pdf.bullet("Biais HTF : bullish (80% impulsion up)")
    pdf.bullet("Zone demande : 712.88 - 714.31")
    pdf.bullet("FVG bullish : 709.62 - 710.62 (confirme la zone)")
    pdf.bullet("Liquidite : externe sweeped (clean, pas d'inducement)")
    pdf.bullet("Market Shift LTF : confirme")
    pdf.bullet("Entree : 712.88 - 714.31")
    pdf.bullet("Stop Loss : 712.74")
    pdf.bullet("Take Profit : 724.34")
    pdf.bullet("Risk/Reward : 12.5 (>> minimum 1:7)")
    pdf.bullet("Confiance : HIGH")
    pdf.bullet("Risque max : $1,000 (1% de $100,000)")
    pdf.title_block("Analyse IA (Featherless / Qwen)", level=2)
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5.5,
        '"Le signal indique un achat sur QQQ a partir de 712.88-714.31 '
        'avec un biais bullish. Les filtres techniques sont tous positifs, '
        'y compris le biais haussier a court terme, la zone de demande, '
        'et la forte volatilite globale. La liquidite externe est nette '
        'et le changement de tendance confirme."'
    )
    pdf.set_text_color(30, 30, 30)
    pdf.ln(4)

    # ---- PROCHAINES ETAPES ------------------------------------------------
    pdf.title_block("Prochaines etapes", level=2)
    pdf.section_line()
    pdf.bullet("Integration CLI Alpaca (obligatoire pour le hackathon)")
    pdf.bullet("Choix des sous-jacents definitifs (SPY, QQQ, AAPL, ...)")
    pdf.bullet("Backtest de la strategie sur historique")
    pdf.bullet("Strategies options : calls/puts directionnels + spreads/condors")
    pdf.bullet("Social engagement (X / LinkedIn avec @lablabai @AlpacaHQ)")
    pdf.bullet("Soumission finale : compte neuf, one-page write-up, video")

    # ---- CONTRAINTES -----------------------------------------------------
    pdf.title_block("Contraintes connues", level=2)
    pdf.section_line()
    pdf.bullet("Flux IEX (gratuit) : ~15 jours d'historique intraday, ~2.7 ans de daily")
    pdf.bullet("Python 3.14 : recent, tous les wheels sont disponibles")
    pdf.bullet("Pour la soumission finale : creer un compte paper NEUF dedie ($100,000)")

    # ---- SAVE ------------------------------------------------------------
    output = "docs/Rapport_31_Aout_2026.pdf"
    pdf.output(output)
    print(f"PDF genere : {output}")
    return output


if __name__ == "__main__":
    build_report()