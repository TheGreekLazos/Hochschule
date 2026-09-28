import pandas as pd
import numpy as np
import tkinter as tk

from tkinter import messagebox, ttk

import seaborn as sns
import matplotlib.pyplot as plt

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
)
from statsmodels.tools.tools import add_constant
import sys
print(sys.executable)
# ==========================================
# EXCEL-DATEI HIER EINTRAGEN
# ==========================================

EXCEL_FILE = (
    "/Daten/Unternehmensdaten.xlsx"
)


# ==========================================
# DATEI LADEN
# ==========================================

try:
    df = pd.read_excel(
        EXCEL_FILE,
        engine="openpyxl"
    )

except Exception as error:
    raise RuntimeError(
        f"Die Excel-Datei konnte nicht geladen werden:\n{error}"
    ) from error


columns = list(df.columns)

# ==========================================
# ERSTELLUNG VON RESIDUEN-PLOTS
# ==========================================
def plot_residuals(fitted_model):

    fitted_values = fitted_model.fittedvalues
    residuals = fitted_model.resid

    plt.figure(figsize=(10, 6))

    plt.scatter(
        fitted_values,
        residuals,
        alpha=0.6
    )

    plt.axhline(
        y=0,
        color="red",
        linestyle="--"
    )

    plt.xlabel("Vorhergesagte Werte")
    plt.ylabel("Residuen")

    plt.title(
        "Residuenplot: Vorhersage vs. Residuen"
    )

    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

# ==========================================
# AUSGEWÄHLTE SPALTEN AUFBEREITEN
# ==========================================

def prepare_selected_data():

    selected_indices = listbox.curselection()

    if len(selected_indices) < 2:
        messagebox.showerror(
            "Fehler",
            "Bitte mindestens zwei Spalten auswählen."
        )
        return None

    selected_columns = [
        columns[index]
        for index in selected_indices
    ]

    analysis_df = df[selected_columns].copy()

    # Ausgewählte Spalten numerisch konvertieren.
    # Nicht numerische Inhalte werden zu NaN.
    for column in analysis_df.columns:
        analysis_df[column] = pd.to_numeric(
            analysis_df[column],
            errors="coerce"
        )

    # Unendliche Werte durch fehlende Werte ersetzen.
    analysis_df = analysis_df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    return analysis_df


# ==========================================
# KORRELATIONSANALYSE
# ==========================================

def run_correlation_analysis():

    analysis_df = prepare_selected_data()

    if analysis_df is None:
        return

    # Zeilen entfernen, in denen alle ausgewählten Werte fehlen.
    analysis_df = analysis_df.dropna(
        how="all"
    )

    # Spalten ohne Varianz identifizieren.
    constant_columns = [
        column
        for column in analysis_df.columns
        if analysis_df[column].nunique(dropna=True) <= 1
    ]

    # Konstante Spalten entfernen.
    analysis_df = analysis_df.drop(
        columns=constant_columns,
        errors="ignore"
    )

    if analysis_df.shape[1] < 2:
        messagebox.showerror(
            "Fehler",
            "Nach der Datenbereinigung sind weniger als "
            "zwei geeignete Variablen vorhanden."
        )
        return

    method = "pearson"

    # Unterstützt Pearson und Spearman.
    corr_matrix = analysis_df.corr(
        method=method
    )

    if corr_matrix.empty:
        messagebox.showerror(
            "Fehler",
            "Die Korrelationsmatrix konnte nicht berechnet werden."
        )
        return

    figure_width = max(
        12,
        len(corr_matrix.columns) * 0.9
    )

    figure_height = max(
        9,
        len(corr_matrix.columns) * 0.7
    )

    plt.figure(
        figsize=(figure_width, figure_height)
    )

    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=0.3
    )

    plt.title(
    "Pearson-Korrelationsmatrix")

    plt.xticks(
        rotation=90
    )

    plt.yticks(
        rotation=0
    )

    plt.tight_layout()
    plt.show()

    # Nur das obere Dreieck der Korrelationsmatrix verwenden,
    # damit jedes Variablenpaar nur einmal erscheint.
    upper_triangle = np.triu(
        np.ones(corr_matrix.shape),
        k=1
    ).astype(bool)

    corr_pairs = (
        corr_matrix
        .where(upper_triangle)
        .stack()
        .reset_index()
    )

    corr_pairs.columns = [
        "Variable 1",
        "Variable 2",
        "Korrelation"
    ]

    corr_pairs["Absolute Korrelation"] = (
        corr_pairs["Korrelation"].abs()
    )

    corr_pairs = corr_pairs.sort_values(
        "Absolute Korrelation",
        ascending=False
    )

    print("\n")
    print("=" * 100)
    print(
        f"STÄRKSTE KORRELATIONEN "
        f"({method.upper()})"
    )
    print("=" * 100)

    if corr_pairs.empty:
        print(
            "Es konnten keine gültigen Variablenpaare "
            "berechnet werden."
        )
    else:
        print(
            corr_pairs[
                [
                    "Variable 1",
                    "Variable 2",
                    "Korrelation"
                ]
            ].head(50).to_string(index=False)
        )


# ==========================================
# VIF-BEWERTUNG
# ==========================================

def classify_vif(vif_value):

    if pd.isna(vif_value):
        return "Nicht berechenbar"

    if np.isinf(vif_value):
        return "Perfekte Multikollinearität"

    if vif_value >= 10:
        return "Sehr kritisch"

    if vif_value >= 5:
        return "Kritisch"

    if vif_value >= 3:
        return "Beobachten"

    return "Unkritisch"


# ==========================================
# VIF-TABELLE IN EINEM NEUEN FENSTER
# ==========================================

def show_vif_table(
    vif_results,
    rows_before,
    rows_after,
    removed_constant_columns
):

    result_window = tk.Toplevel(root)

    result_window.title(
        "VIF-Ergebnisse"
    )

    result_window.geometry(
        "850x600"
    )

    heading = tk.Label(
        result_window,
        text="Variance Inflation Factor",
        font=("Arial", 16, "bold")
    )

    heading.pack(
        pady=(15, 5)
    )

    information_text = (
        f"Datensätze vor Bereinigung: {rows_before:,}\n"
        f"Datensätze für VIF verwendet: {rows_after:,}\n"
        f"Entfernte Datensätze: {rows_before - rows_after:,}"
    )

    if removed_constant_columns:
        information_text += (
            "\nKonstante Spalten entfernt: "
            + ", ".join(removed_constant_columns)
        )

    information_label = tk.Label(
        result_window,
        text=information_text,
        justify=tk.LEFT
    )

    information_label.pack(
        pady=(0, 10)
    )

    table_frame = tk.Frame(
        result_window
    )

    table_frame.pack(
        fill=tk.BOTH,
        expand=True,
        padx=15,
        pady=10
    )

    table = ttk.Treeview(
        table_frame,
        columns=(
            "Variable",
            "VIF",
            "Bewertung"
        ),
        show="headings"
    )

    table.heading(
        "Variable",
        text="Variable"
    )

    table.heading(
        "VIF",
        text="VIF"
    )

    table.heading(
        "Bewertung",
        text="Bewertung"
    )

    table.column(
        "Variable",
        width=400,
        anchor=tk.W
    )

    table.column(
        "VIF",
        width=120,
        anchor=tk.CENTER
    )

    table.column(
        "Bewertung",
        width=220,
        anchor=tk.CENTER
    )

    vertical_scrollbar = ttk.Scrollbar(
        table_frame,
        orient=tk.VERTICAL,
        command=table.yview
    )

    table.configure(
        yscrollcommand=vertical_scrollbar.set
    )

    table.pack(
        side=tk.LEFT,
        fill=tk.BOTH,
        expand=True
    )

    vertical_scrollbar.pack(
        side=tk.RIGHT,
        fill=tk.Y
    )

    # Farben für die VIF-Bewertungen.
    table.tag_configure(
        "Unkritisch",
        background="#C6EFCE"
    )

    table.tag_configure(
        "Beobachten",
        background="#FFEB9C"
    )

    table.tag_configure(
        "Kritisch",
        background="#F4B084"
    )

    table.tag_configure(
        "Sehr kritisch",
        background="#F8696B",
        foreground="white"
    )

    table.tag_configure(
        "Perfekte Multikollinearität",
        background="#9C0006",
        foreground="white"
    )

    table.tag_configure(
        "Nicht berechenbar",
        background="#D9D9D9"
    )

    for _, row in vif_results.iterrows():

        vif_value = row["VIF"]

        if np.isinf(vif_value):
            displayed_vif = "Unendlich"

        elif pd.isna(vif_value):
            displayed_vif = "Nicht berechenbar"

        else:
            displayed_vif = f"{vif_value:.2f}"

        table.insert(
            "",
            tk.END,
            values=(
                row["Variable"],
                displayed_vif,
                row["Bewertung"]
            ),
            tags=(
                row["Bewertung"],
            )
        )

    legend_text = (
        "Interpretation: "
        "VIF < 3 = unkritisch | "
        "3 bis < 5 = beobachten | "
        "5 bis < 10 = kritisch | "
        "ab 10 = sehr kritisch"
    )

    legend = tk.Label(
        result_window,
        text=legend_text,
        font=("Arial", 10)
    )

    legend.pack(
        pady=(5, 15)
    )


# ==========================================
# VIF-CHECK
# ==========================================

def run_vif_analysis():

    analysis_df = prepare_selected_data()

    if analysis_df is None:
        return

    rows_before = len(
        analysis_df
    )

    # Der VIF benötigt vollständige Datensätze.
    # Jede Zeile mit mindestens einem fehlenden Wert
    # in den ausgewählten Features wird entfernt.
    vif_df = analysis_df.dropna(
        axis=0,
        how="any"
    ).copy()

    rows_after = len(
        vif_df
    )

    if vif_df.empty:
        messagebox.showerror(
            "VIF-Fehler",
            "Nach dem Entfernen fehlender Werte sind "
            "keine vollständigen Datensätze mehr vorhanden."
        )
        return

    # Spalten ohne Varianz identifizieren.
    constant_columns = [
        column
        for column in vif_df.columns
        if vif_df[column].nunique(dropna=True) <= 1
    ]

    # Konstante Spalten entfernen.
    if constant_columns:
        vif_df = vif_df.drop(
            columns=constant_columns
        )

    if vif_df.shape[1] < 2:
        messagebox.showerror(
            "VIF-Fehler",
            "Nach dem Entfernen konstanter Spalten "
            "sind weniger als zwei Features übrig."
        )
        return

    # VIF wird instabil, wenn nicht mehr vollständige
    # Datensätze als ausgewählte Features vorhanden sind.
    # VIF wird instabil, wenn nicht mehr vollständige
# Datensätze als ausgewählte Variablen vorhanden sind.
    if vif_df.shape[0] <= vif_df.shape[1]:
        messagebox.showerror(
            "VIF-Fehler",
            "Für den VIF-Check müssen mehr vollständige "
            "Datensätze als ausgewählte Variablen vorhanden sein."
        )
        return


    # Prüfen, ob doppelte Spalten vorhanden sind.
    duplicate_columns = vif_df.columns[
        vif_df.columns.duplicated()
    ].tolist()

    if duplicate_columns:
        messagebox.showerror(
            "VIF-Fehler",
            "Die Auswahl enthält doppelte Spaltennamen:\n"
            + ", ".join(duplicate_columns)
        )
        return

    # Datentyp für Statsmodels vereinheitlichen.
    vif_df = vif_df.astype(float)

    # Konstante für die Regressionsberechnung ergänzen.
    vif_with_constant = add_constant(
        vif_df,
        has_constant="add"
    )

    vif_results = []

    for column_index, column_name in enumerate(
        vif_with_constant.columns
    ):

        # Technische Regressionskonstante
        # nicht in der Ergebnistabelle anzeigen.
        if column_name == "const":
            continue

        try:
            vif_value = variance_inflation_factor(
                vif_with_constant.values,
                column_index
            )

        except Exception as error:
            print(
                f"VIF für '{column_name}' konnte nicht "
                f"berechnet werden: {error}"
            )
            vif_value = np.nan

        vif_results.append(
            {
                "Variable": column_name,
                "VIF": vif_value,
                "Bewertung": classify_vif(vif_value)
            }
        )

    vif_result_df = pd.DataFrame(
        vif_results
    )

    if vif_result_df.empty:
        messagebox.showerror(
            "VIF-Fehler",
            "Es konnten keine VIF-Werte berechnet werden."
        )
        return

    # Unendliche und hohe Werte zuerst anzeigen.
    vif_result_df["Sortierwert"] = (
        vif_result_df["VIF"]
        .replace(
            [np.inf, -np.inf],
            999999999
        )
        .fillna(-1)
    )

    vif_result_df = (
        vif_result_df
        .sort_values(
            "Sortierwert",
            ascending=False
        )
        .drop(
            columns="Sortierwert"
        )
        .reset_index(
            drop=True
        )
    )

    # Ausgabe im Terminal.
    print("\n")
    print("=" * 100)
    print("VIF-CHECK")
    print("=" * 100)

    terminal_output = vif_result_df.copy()

    terminal_output["VIF"] = terminal_output["VIF"].apply(
        lambda value: (
            "Unendlich"
            if np.isinf(value)
            else (
                "Nicht berechenbar"
                if pd.isna(value)
                else f"{value:.2f}"
            )
        )
    )

    print(
        terminal_output.to_string(
            index=False
        )
    )

    # Grafische Tabelle anzeigen.
    show_vif_table(
        vif_results=vif_result_df,
        rows_before=rows_before,
        rows_after=rows_after,
        removed_constant_columns=constant_columns
    )


# ==========================================
# AUSWAHL ZURÜCKSETZEN
# ==========================================

def clear_selection():

    listbox.selection_clear(
        0,
        tk.END
    )


# ==========================================
# ALLE SPALTEN AUSWÄHLEN
# ==========================================

def select_all_columns():

    listbox.selection_set(
        0,
        tk.END
    )


# ==========================================
# GUI
# ==========================================

root = tk.Tk()

root.title(
    "Korrelationsanalyse und VIF-Check"
)

root.geometry(
    "760x800"
)


label = tk.Label(
    root,
    text=(
        "Spalten für Korrelationsanalyse "
        "oder VIF-Check auswählen"
    ),
    font=("Arial", 14, "bold")
)

label.pack(
    pady=(15, 5)
)


selection_information = tk.Label(
    root,
    text=(
        "Mehrfachauswahl auf macOS: "
        "Command-Taste gedrückt halten"
    ),
    fg="gray"
)

selection_information.pack(
    pady=(0, 10)
)


list_frame = tk.Frame(
    root
)

list_frame.pack(
    fill=tk.BOTH,
    expand=True,
    padx=20,
    pady=5
)


listbox = tk.Listbox(
    list_frame,
    selectmode=tk.MULTIPLE,
    width=75,
    height=27,
    exportselection=False
)


scrollbar = ttk.Scrollbar(
    list_frame,
    orient=tk.VERTICAL,
    command=listbox.yview
)


listbox.configure(
    yscrollcommand=scrollbar.set
)


for column in columns:
    listbox.insert(
        tk.END,
        column
    )


listbox.pack(
    side=tk.LEFT,
    fill=tk.BOTH,
    expand=True
)


scrollbar.pack(
    side=tk.RIGHT,
    fill=tk.Y
)


# ==========================================
# AUSWAHL-BUTTONS
# ==========================================

selection_button_frame = tk.Frame(
    root
)

selection_button_frame.pack(
    pady=5
)


tk.Button(
    selection_button_frame,
    text="Alle auswählen",
    command=select_all_columns,
    width=18
).pack(
    side=tk.LEFT,
    padx=5
)


tk.Button(
    selection_button_frame,
    text="Auswahl löschen",
    command=clear_selection,
    width=18
).pack(
    side=tk.LEFT,
    padx=5
)









# ==========================================
# ANALYSE-BUTTONS
# ==========================================

button_frame = tk.Frame(
    root
)

button_frame.pack(
    pady=(5, 20)
)


tk.Button(
    button_frame,
    text="Korrelationsmatrix",
    command=run_correlation_analysis,
    bg="#228B22",
    fg="white",
    width=26,
    height=2
).pack(
    side=tk.LEFT,
    padx=8
)


tk.Button(
    button_frame,
    text="VIF-Check",
    command=run_vif_analysis,
    bg="#1565C0",
    fg="white",
    width=26,
    height=2
).pack(
    side=tk.LEFT,
    padx=8
)

import warnings
import tkinter as tk

from tkinter import messagebox, ttk

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
)


# ==========================================
# EINSTELLUNGEN
# ==========================================

EXCEL_FILE = (
    "/Daten/Unternehmensdaten.xlsx"
)

# Falls deine NPS-Spalte anders heißt, hier anpassen.
DEFAULT_TARGET_COLUMN = "Gesamt NPS"

# Excel-Tabellenblatt:
# 0 = erstes Tabellenblatt
EXCEL_SHEET = 0

# Signifikanzniveau
ALPHA = 0.05


# ==========================================
# EXCEL-DATEI LADEN
# ==========================================

try:
    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name=EXCEL_SHEET,
        engine="openpyxl"
    )

except Exception as error:
    raise RuntimeError(
        f"Die Excel-Datei konnte nicht geladen werden:\n{error}"
    ) from error


# Leerzeichen aus Spaltennamen entfernen.
df.columns = [
    str(column).strip()
    for column in df.columns
]


# Zeichencodierungsfehler aus Excel bei Bedarf korrigieren.
df = df.rename(
    columns={
        "Bruttost√∂rdauer": "Bruttostördauer",
        "Nettost√∂rdauer": "Nettostördauer"
    }
)


columns = list(df.columns)


# ==========================================
# HILFSFUNKTIONEN
# ==========================================

def classify_beta(beta_value):

    if pd.isna(beta_value):
        return "Nicht berechenbar"

    absolute_beta = abs(beta_value)

    if absolute_beta < 0.10:
        return "Sehr schwach"

    if absolute_beta < 0.30:
        return "Schwach"

    if absolute_beta < 0.50:
        return "Mittel"

    if absolute_beta < 0.70:
        return "Stark"

    return "Sehr stark"


def classify_direction(beta_value):

    if pd.isna(beta_value):
        return "Nicht berechenbar"

    if beta_value > 0:
        return "Positiv"

    if beta_value < 0:
        return "Negativ"

    return "Keine Richtung"


def format_number(value, decimal_places=4):

    if pd.isna(value):
        return "n. b."

    if np.isinf(value):
        return "Unendlich"

    return f"{value:.{decimal_places}f}"


def format_p_value(value):

    if pd.isna(value):
        return "n. b."

    if value < 0.0001:
        return "< 0,0001"

    return f"{value:.4f}"


def get_selected_features():

    selected_indices = feature_listbox.curselection()

    selected_features = [
        columns[index]
        for index in selected_indices
    ]

    return selected_features


# ==========================================
# DATEN AUFBEREITEN
# ==========================================

def prepare_regression_data(
    target_column,
    selected_features
):

    if target_column not in df.columns:
        raise ValueError(
            f"Die Zielvariable '{target_column}' "
            "existiert nicht in der Excel-Datei."
        )

    if target_column in selected_features:
        selected_features = [
            feature
            for feature in selected_features
            if feature != target_column
        ]

    if len(selected_features) < 1:
        raise ValueError(
            "Bitte mindestens ein erklärendes Feature auswählen."
        )

    regression_df = df[
        [target_column] + selected_features
    ].copy()

    # Zielvariable numerisch konvertieren.
    regression_df[target_column] = pd.to_numeric(
        regression_df[target_column],
        errors="coerce"
    )

    # Features numerisch konvertieren.
    for feature in selected_features:
        regression_df[feature] = pd.to_numeric(
            regression_df[feature],
            errors="coerce"
        )

    regression_df = regression_df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    rows_before = len(regression_df)

    # Für die Regression werden nur vollständige Zeilen verwendet.
    regression_df = regression_df.dropna(
        axis=0,
        how="any"
    ).copy()

    rows_after_missing = len(regression_df)

    # Konstante Features identifizieren.
    constant_features = [
        feature
        for feature in selected_features
        if regression_df[feature].nunique(
            dropna=True
        ) <= 1
    ]

    if constant_features:
        regression_df = regression_df.drop(
            columns=constant_features
        )

        selected_features = [
            feature
            for feature in selected_features
            if feature not in constant_features
        ]

    if len(selected_features) < 1:
        raise ValueError(
            "Nach dem Entfernen konstanter Spalten "
            "ist kein geeignetes Feature mehr vorhanden."
        )

    if regression_df[target_column].nunique() <= 1:
        raise ValueError(
            "Die NPS-Zielvariable besitzt keine ausreichende "
            "Varianz für eine Regression."
        )

    if len(regression_df) <= len(selected_features) + 1:
        raise ValueError(
            "Für die Regression müssen mehr vollständige "
            "Datensätze als Modellparameter vorhanden sein."
        )

    return (
        regression_df,
        selected_features,
        constant_features,
        rows_before,
        rows_after_missing
    )


# ==========================================
# VIF BERECHNEN
# ==========================================

def calculate_vif(feature_df):

    vif_data = feature_df.copy()

    # Regressionskonstante ergänzen.
    vif_with_constant = sm.add_constant(
        vif_data,
        has_constant="add"
    )

    vif_results = []

    for column_index, column_name in enumerate(
        vif_with_constant.columns
    ):

        if column_name == "const":
            continue

        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "ignore"
                )

                vif_value = variance_inflation_factor(
                    vif_with_constant.values,
                    column_index
                )

        except Exception:
            vif_value = np.nan

        vif_results.append(
            {
                "Feature": column_name,
                "VIF": vif_value
            }
        )

    return pd.DataFrame(
        vif_results
    )


# ==========================================
# MULTIPLE LINEARE REGRESSION
# ==========================================

def calculate_multiple_regression(
    target_column,
    selected_features
):

    (
        regression_df,
        valid_features,
        constant_features,
        rows_before,
        rows_after
    ) = prepare_regression_data(
        target_column,
        selected_features
    )

    y_original = regression_df[
        target_column
    ].astype(float)

    x_original = regression_df[
        valid_features
    ].astype(float)

    # Mittelwerte und Standardabweichungen.
    x_means = x_original.mean()
    x_standard_deviations = x_original.std(
        ddof=0
    )

    y_mean = y_original.mean()
    y_standard_deviation = y_original.std(
        ddof=0
    )

    if y_standard_deviation == 0:
        raise ValueError(
            "Die NPS-Zielvariable besitzt eine "
            "Standardabweichung von 0."
        )

    # Alle erklärenden Features standardisieren.
    x_standardized = (
        x_original - x_means
    ) / x_standard_deviations

    # Auch NPS standardisieren.
    # Dadurch sind die Koeffizienten standardisierte Betas.
    y_standardized = (
        y_original - y_mean
    ) / y_standard_deviation

    x_standardized = x_standardized.replace(
        [np.inf, -np.inf],
        np.nan
    )

    if x_standardized.isna().any().any():
        raise ValueError(
            "Mindestens ein Feature konnte nicht korrekt "
            "standardisiert werden."
        )

    # Regressionskonstante ergänzen.
    x_model = sm.add_constant(
        x_standardized,
        has_constant="add"
    )

    # OLS-Modell mit robusten Standardfehlern.
    model = sm.OLS(
        y_standardized,
        x_model
    )

    fitted_model = model.fit(
        cov_type="HC3"
    )

    confidence_intervals = fitted_model.conf_int(
        alpha=ALPHA
    )

    regression_results = []

    for feature in valid_features:

        beta = fitted_model.params.get(
            feature,
            np.nan
        )

        standard_error = fitted_model.bse.get(
            feature,
            np.nan
        )

        t_value = fitted_model.tvalues.get(
            feature,
            np.nan
        )

        p_value = fitted_model.pvalues.get(
            feature,
            np.nan
        )

        if feature in confidence_intervals.index:
            ci_lower = confidence_intervals.loc[
                feature,
                0
            ]

            ci_upper = confidence_intervals.loc[
                feature,
                1
            ]

        else:
            ci_lower = np.nan
            ci_upper = np.nan

        regression_results.append(
            {
                "Feature": feature,
                "Beta": beta,
                "Standardfehler": standard_error,
                "t-Wert": t_value,
                "p-Wert": p_value,
                "KI Untergrenze": ci_lower,
                "KI Obergrenze": ci_upper,
                "Richtung": classify_direction(beta),
                "Stärke": classify_beta(beta),
                "Signifikant": (
                    "Ja"
                    if not pd.isna(p_value)
                    and p_value < ALPHA
                    else "Nein"
                )
            }
        )

    regression_result_df = pd.DataFrame(
        regression_results
    )

    vif_result_df = calculate_vif(
        x_original
    )

    regression_result_df = regression_result_df.merge(
        vif_result_df,
        on="Feature",
        how="left"
    )

    regression_result_df[
        "Absolutes Beta"
    ] = regression_result_df[
        "Beta"
    ].abs()

    regression_result_df = (
        regression_result_df
        .sort_values(
            "Absolutes Beta",
            ascending=False
        )
        .drop(
            columns="Absolutes Beta"
        )
        .reset_index(
            drop=True
        )
    )

    model_information = {
        "Datensätze vorher": rows_before,
        "Datensätze verwendet": rows_after,
        "Datensätze entfernt": (
            rows_before - rows_after
        ),
        "Anzahl Features": len(valid_features),
        "R²": fitted_model.rsquared,
        "Adjustiertes R²": fitted_model.rsquared_adj,
        "F-Statistik": fitted_model.fvalue,
        "F-p-Wert": fitted_model.f_pvalue,
        "AIC": fitted_model.aic,
        "BIC": fitted_model.bic,
        "Konstante Features": constant_features
    }

    return (
        regression_result_df,
        fitted_model,
        model_information
    )


# ==========================================
# TERMINALAUSGABE
# ==========================================

def print_regression_results(
    result_df,
    fitted_model,
    model_information
):

    print("\n")
    print("=" * 120)
    print("MULTIPLE LINEARE REGRESSION")
    print("=" * 120)

    print(
        f"Verwendete Datensätze: "
        f"{model_information['Datensätze verwendet']:,}"
    )

    print(
        f"Entfernte Datensätze wegen fehlender Werte: "
        f"{model_information['Datensätze entfernt']:,}"
    )

    print(
        f"Anzahl Features: "
        f"{model_information['Anzahl Features']}"
    )

    print(
        f"R²: "
        f"{model_information['R²']:.4f}"
    )

    print(
        f"Adjustiertes R²: "
        f"{model_information['Adjustiertes R²']:.4f}"
    )

    print(
        f"F-p-Wert: "
        f"{model_information['F-p-Wert']:.6f}"
    )

    if model_information["Konstante Features"]:

        print(
            "Entfernte konstante Features: "
            + ", ".join(
                model_information[
                    "Konstante Features"
                ]
            )
        )

    terminal_df = result_df.copy()

    for column in [
        "Beta",
        "Standardfehler",
        "t-Wert",
        "KI Untergrenze",
        "KI Obergrenze",
        "VIF"
    ]:
        terminal_df[column] = terminal_df[column].apply(
            lambda value: format_number(
                value,
                4
            )
        )

    terminal_df["p-Wert"] = terminal_df[
        "p-Wert"
    ].apply(
        format_p_value
    )

    print("\n")

    print(
        terminal_df[
            [
                "Feature",
                "Beta",
                "Standardfehler",
                "t-Wert",
                "p-Wert",
                "KI Untergrenze",
                "KI Obergrenze",
                "VIF",
                "Richtung",
                "Stärke",
                "Signifikant"
            ]
        ].to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 120)
    print("VOLLSTÄNDIGE STATSMODELS-AUSGABE")
    print("=" * 120)

    print(
        fitted_model.summary()
    )


# ==========================================
# REGRESSIONSGRAFIK
# ==========================================

def plot_regression_results(
    result_df,
    target_column,
    model_information
):

    plot_df = result_df.copy()

    plot_df = plot_df.sort_values(
        "Beta",
        ascending=True
    )

    colors = [
        "#228B22"
        if beta >= 0
        else "#D12B2B"
        for beta in plot_df["Beta"]
    ]

    figure_height = max(
        7,
        len(plot_df) * 0.65
    )

    figure, axis = plt.subplots(
        figsize=(15, figure_height)
    )

    bars = axis.barh(
        plot_df["Feature"],
        plot_df["Beta"],
        color=colors,
        alpha=0.95
    )

    axis.axvline(
        0,
        color="black",
        linewidth=1.2
    )

    # Konfidenzintervalle als Fehlerbalken.
    lower_errors = (
        plot_df["Beta"]
        - plot_df["KI Untergrenze"]
    ).clip(lower=0)

    upper_errors = (
        plot_df["KI Obergrenze"]
        - plot_df["Beta"]
    ).clip(lower=0)

    axis.errorbar(
        plot_df["Beta"],
        np.arange(len(plot_df)),
        xerr=[
            lower_errors,
            upper_errors
        ],
        fmt="none",
        ecolor="black",
        elinewidth=1.2,
        capsize=4
    )

    all_values = pd.concat(
        [
            plot_df["KI Untergrenze"],
            plot_df["KI Obergrenze"],
            plot_df["Beta"]
        ]
    ).dropna()

    if not all_values.empty:

        maximum_absolute_value = max(
            abs(all_values.min()),
            abs(all_values.max())
        )

        x_limit = max(
            0.2,
            maximum_absolute_value * 1.25
        )

        axis.set_xlim(
            -x_limit,
            x_limit
        )

    axis.set_xlabel(
        "Standardisierter Regressionskoeffizient Beta"
    )

    axis.set_ylabel(
        "Ticketfeature"
    )

    axis.set_title(
        f"Gemeinsamer Zusammenhang der Ticketfeatures "
        f"mit {target_column}\n"
        f"R² = {model_information['R²']:.3f} | "
        f"Adjustiertes R² = "
        f"{model_information['Adjustiertes R²']:.3f}"
    )

    for bar, beta, p_value in zip(
        bars,
        plot_df["Beta"],
        plot_df["p-Wert"]
    ):

        if pd.isna(beta):
            continue

        significance_marker = (
            "*"
            if not pd.isna(p_value)
            and p_value < ALPHA
            else ""
        )

        label = (
            f"{beta:.3f}"
            f"{significance_marker}"
        )

        x_offset = (
            0.01
            if beta >= 0
            else -0.01
        )

        horizontal_alignment = (
            "left"
            if beta >= 0
            else "right"
        )

        axis.text(
            beta + x_offset,
            bar.get_y()
            + bar.get_height() / 2,
            label,
            va="center",
            ha=horizontal_alignment,
            fontsize=10
        )

    axis.grid(
        axis="x",
        alpha=0.25
    )

    figure.text(
        0.01,
        0.01,
        "* p < 0,05 | Schwarze Linien zeigen "
        "95-%-Konfidenzintervalle",
        fontsize=10
    )

    plt.tight_layout(
        rect=[
            0,
            0.035,
            1,
            1
        ]
    )

    plt.show()


# ==========================================
# ERGEBNISTABELLE IN DER GUI
# ==========================================

def show_result_table(
    result_df,
    target_column,
    model_information
):

    result_window = tk.Toplevel(
        root
    )

    result_window.title(
        "Ergebnisse der multiplen linearen Regression"
    )

    result_window.geometry(
        "1450x750"
    )

    heading = tk.Label(
        result_window,
        text=(
            "Multiple lineare Regression "
            f"für {target_column}"
        ),
        font=(
            "Arial",
            16,
            "bold"
        )
    )

    heading.pack(
        pady=(15, 5)
    )

    information_text = (
        f"Verwendete Datensätze: "
        f"{model_information['Datensätze verwendet']:,}\n"
        f"Entfernte Datensätze: "
        f"{model_information['Datensätze entfernt']:,}\n"
        f"R²: {model_information['R²']:.4f} | "
        f"Adjustiertes R²: "
        f"{model_information['Adjustiertes R²']:.4f} | "
        f"Modell-p-Wert: "
        f"{model_information['F-p-Wert']:.6f}"
    )

    information_label = tk.Label(
        result_window,
        text=information_text,
        justify=tk.LEFT
    )

    information_label.pack(
        pady=(0, 10)
    )

    table_frame = tk.Frame(
        result_window
    )

    table_frame.pack(
        fill=tk.BOTH,
        expand=True,
        padx=15,
        pady=10
    )

    table_columns = (
        "Feature",
        "Beta",
        "p-Wert",
        "KI 95 % unten",
        "KI 95 % oben",
        "VIF",
        "Richtung",
        "Stärke",
        "Signifikant"
    )

    table = ttk.Treeview(
        table_frame,
        columns=table_columns,
        show="headings"
    )

    widths = {
        "Feature": 300,
        "Beta": 100,
        "p-Wert": 100,
        "KI 95 % unten": 120,
        "KI 95 % oben": 120,
        "VIF": 100,
        "Richtung": 100,
        "Stärke": 110,
        "Signifikant": 100
    }

    for column in table_columns:

        table.heading(
            column,
            text=column
        )

        table.column(
            column,
            width=widths[column],
            anchor=(
                tk.W
                if column == "Feature"
                else tk.CENTER
            )
        )

    vertical_scrollbar = ttk.Scrollbar(
        table_frame,
        orient=tk.VERTICAL,
        command=table.yview
    )

    horizontal_scrollbar = ttk.Scrollbar(
        table_frame,
        orient=tk.HORIZONTAL,
        command=table.xview
    )

    table.configure(
        yscrollcommand=vertical_scrollbar.set,
        xscrollcommand=horizontal_scrollbar.set
    )

    table.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    vertical_scrollbar.grid(
        row=0,
        column=1,
        sticky="ns"
    )

    horizontal_scrollbar.grid(
        row=1,
        column=0,
        sticky="ew"
    )

    table_frame.grid_rowconfigure(
        0,
        weight=1
    )

    table_frame.grid_columnconfigure(
        0,
        weight=1
    )

    table.tag_configure(
        "Signifikant positiv",
        background="#C6EFCE"
    )

    table.tag_configure(
        "Signifikant negativ",
        background="#F4CCCC"
    )

    table.tag_configure(
        "Nicht signifikant",
        background="#E7E6E6"
    )

    for _, row in result_df.iterrows():

        if row["Signifikant"] == "Ja":

            if row["Beta"] >= 0:
                table_tag = "Signifikant positiv"

            else:
                table_tag = "Signifikant negativ"

        else:
            table_tag = "Nicht signifikant"

        table.insert(
            "",
            tk.END,
            values=(
                row["Feature"],
                format_number(
                    row["Beta"]
                ),
                format_p_value(
                    row["p-Wert"]
                ),
                format_number(
                    row["KI Untergrenze"]
                ),
                format_number(
                    row["KI Obergrenze"]
                ),
                format_number(
                    row["VIF"],
                    2
                ),
                row["Richtung"],
                row["Stärke"],
                row["Signifikant"]
            ),
            tags=(
                table_tag,
            )
        )

    explanation_label = tk.Label(
        result_window,
        text=(
            "Interpretation: Beta zeigt Richtung und relative "
            "Stärke des Zusammenhangs unter Kontrolle der "
            "anderen Features. Ein Stern bzw. Signifikant = Ja "
            "bedeutet p < 0,05. Ein Konfidenzintervall, das 0 "
            "enthält, spricht gegen einen statistisch eindeutigen "
            "Koeffizienten."
        ),
        wraplength=1300,
        justify=tk.LEFT
    )

    explanation_label.pack(
        pady=(5, 15)
    )


# ==========================================
# REGRESSION STARTEN
# ==========================================

def run_regression():

    target_column = target_combobox.get().strip()

    selected_features = get_selected_features()

    if not target_column:
        messagebox.showerror(
            "Fehler",
            "Bitte eine NPS-Zielvariable auswählen."
        )
        return

    if target_column in selected_features:
        selected_features = [
            feature
            for feature in selected_features
            if feature != target_column
        ]

    if len(selected_features) < 1:
        messagebox.showerror(
            "Fehler",
            "Bitte mindestens ein erklärendes "
            "Ticketfeature auswählen."
        )
        return

    try:
        (
            result_df,
            fitted_model,
            model_information
        ) = calculate_multiple_regression(
            target_column=target_column,
            selected_features=selected_features
        )

    except Exception as error:
        messagebox.showerror(
            "Regressionsfehler",
            str(error)
        )
        return

    print_regression_results(
        result_df=result_df,
        fitted_model=fitted_model,
        model_information=model_information
    )

    show_result_table(
        result_df=result_df,
        target_column=target_column,
        model_information=model_information
    )

    plot_regression_results(
        result_df=result_df,
        target_column=target_column,
        model_information=model_information
    )
    plot_residuals(
    fitted_model
)


# ==========================================
# AUSWAHLFUNKTIONEN
# ==========================================

def select_all_features():

    feature_listbox.selection_set(
        0,
        tk.END
    )

    target_column = target_combobox.get()

    if target_column in columns:

        target_index = columns.index(
            target_column
        )

        feature_listbox.selection_clear(
            target_index
        )


def clear_feature_selection():

    feature_listbox.selection_clear(
        0,
        tk.END
    )


# ==========================================
# GUI
# ==========================================

regression_window = tk.Toplevel(root)

regression_window.title(
    "Multiple lineare Regression für NPS"
)

regression_window.geometry(
    "800x850"
)


heading_label = tk.Label(
    regression_window,
    text=(
        "Gemeinsamer Zusammenhang der "
        "Ticketfeatures mit dem NPS"
    ),
    font=(
        "Arial",
        15,
        "bold"
    )
)

heading_label.pack(
    pady=(15, 10)
)


# ==========================================
# ZIELVARIABLE
# ==========================================

target_frame = tk.Frame(
    regression_window
)

target_frame.pack(
    fill=tk.X,
    padx=20,
    pady=5
)


target_label = tk.Label(
    target_frame,
    text="NPS-Zielvariable:"
)

target_label.pack(
    side=tk.LEFT,
    padx=(0, 10)
)


target_combobox = ttk.Combobox(
    target_frame,
    values=columns,
    state="readonly",
    width=45
)

target_combobox.pack(
    side=tk.LEFT
)


if DEFAULT_TARGET_COLUMN in columns:

    target_combobox.set(
        DEFAULT_TARGET_COLUMN
    )

elif "NPS" in columns:

    target_combobox.set(
        "NPS"
    )

else:

    target_combobox.current(
        0
    )


# ==========================================
# FEATURE-AUSWAHL
# ==========================================

feature_label = tk.Label(
    regression_window,
    text=(
        "Erklärende Ticketfeatures auswählen\n"
        "Mehrfachauswahl auf macOS mit Command-Taste"
    ),
    justify=tk.CENTER
)

feature_label.pack(
    pady=(10, 5)
)


list_frame = tk.Frame(
    regression_window
)

list_frame.pack(
    fill=tk.BOTH,
    expand=True,
    padx=20,
    pady=5
)


feature_listbox = tk.Listbox(
    list_frame,
    selectmode=tk.MULTIPLE,
    width=80,
    height=30,
    exportselection=False
)


vertical_scrollbar = ttk.Scrollbar(
    list_frame,
    orient=tk.VERTICAL,
    command=feature_listbox.yview
)


feature_listbox.configure(
    yscrollcommand=vertical_scrollbar.set
)


for column in columns:

    feature_listbox.insert(
        tk.END,
        column
    )


feature_listbox.pack(
    side=tk.LEFT,
    fill=tk.BOTH,
    expand=True
)


vertical_scrollbar.pack(
    side=tk.RIGHT,
    fill=tk.Y
)


# ==========================================
# AUSWAHL-BUTTONS
# ==========================================

selection_button_frame = tk.Frame(
    regression_window
)

selection_button_frame.pack(
    pady=8
)


tk.Button(
    selection_button_frame,
    text="Alle auswählen",
    command=select_all_features,
    width=18
).pack(
    side=tk.LEFT,
    padx=5
)


tk.Button(
    selection_button_frame,
    text="Auswahl löschen",
    command=clear_feature_selection,
    width=18
).pack(
    side=tk.LEFT,
    padx=5
)


# ==========================================
# START-BUTTON
# ==========================================

tk.Button(
    regression_window,
    text="Multiple Regression starten",
    command=run_regression,
    bg="#1565C0",
    fg="white",
    width=32,
    height=2,
    font=(
        "Arial",
        12,
        "bold"
    )
).pack(
    pady=(5, 20)
)


root.mainloop()
