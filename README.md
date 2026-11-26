# Public Services Signal Lab

A dependency-free, reproducible triage tool for daily service delays. It tells an operations team which queues merit a closer look, without pretending to diagnose causes or treating missing reports as zero delays.

## Run the fictional example

Requires Python 3.10+. Nothing to install.

```sh
python signal_lab.py demo.csv --date 2025-03-05 --output report.json
python -m unittest -v
```

The fictional **permit-intake** queue is flagged for review. **street-repairs** is monitored; **library-support** has too little volume; **records-desk** has no observation. Recreate the input with `python make_demo.py`. No actual government data, customer records, or model outcomes are represented.

## Input and decision rule

Use one UTF-8 CSV row per service and calendar day, with `service,date,opened,late`. Each denominator is the number of eligible requests in the same day's cohort; `late` uses one consistent operational deadline. Upstream processing must resolve cohort censoring and revisions before producing the counts.

1. Use only prior dates in a 56-day window and match weekdays. Estimate the historical rate using the median of daily rates; use the scaled median absolute deviation for variability.
2. Require at least five comparison days and 50 current requests. Surface missing and low-information data explicitly.
3. Compare the **lower Wilson bound** of the current binomial late rate with the median plus the larger of a practical four-point threshold and three scaled deviations.
4. Sort flagged queues by estimated excess cases against baseline to aid investigation. Include a source SHA-256 and full configuration in the JSON.

## Scope and limitations

This is a screening heuristic, not a calibrated formal false-alarm rate. The Wilson interval reflects binomial uncertainty for the current numerator, not uncertainty in the baseline or correlation within cohorts. Holidays, mix changes, autocorrelation, multiple comparisons, and upstream definitions can change the operational interpretation. Reconcile those before taking action. No real data or deployed system is claimed.
