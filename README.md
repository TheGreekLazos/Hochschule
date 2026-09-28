# Hinweise
Dieses Repository wird für die Abgabe von Praxisprojekt 6 verwendet.

Zur Ausführung des Programms werden Python 3 sowie die Bibliotheken pandas, numpy, openpyxl, matplotlib, seaborn und statsmodels benötigt. Die erforderlichen Bibliotheken können über das Terminal mit python3 -m pip install pandas numpy openpyxl matplotlib seaborn statsmodels installiert werden oder über die requirements.txt Datei mit dem Befehl python3 -m pip install -r requirements.txt

Vor der Ausführung muss der in EXCEL_FILE hinterlegte Dateipfad an den Speicherort der verwendeten Excel-Datei angepasst werden. Das Programm wird anschließend über das Terminal mit python3 correlation_M.py gestartet.

Mit der Ausführung öffnen zunächst 2 überlappende Programmfenster. Im ersten Programmfenster können mindestens zwei numerische Variablen ausgewählt und anschließend entweder die Pearson-Korrelationsmatrix oder der VIF-Check ausgeführt werden. Im zweiten Programmfenster wird zunächst die NPS-Zielvariable und danach mindestens ein erklärendes Ticketmerkmal ausgewählt. Über die Schaltfläche „Multiple Regression starten“ werden die Regressionsergebnisse, die Koeffizientengrafik und der Residuenplot erzeugt. Die ausgewählten Merkmale dürfen nicht die NPS-Zielvariable enthalten.

Die numerischen Ergebnisse werden zum Teil im Terminal und zum Teil in separaten Programmfenstern ausgegeben. Grafische Ausgaben werden nacheinander dargestellt. Daher muss gegebenenfalls zunächst eine geöffnete Grafik geschlossen werden, bevor die nächste Abbildung erscheint.
