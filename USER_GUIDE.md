# User guide

Jyotish V1.8 — a Vedic astrology calculator that runs on your own
machine and shows its working.

This guide assumes you want to cast and read a chart. It assumes nothing
about how the program is built; if you want that, read
[TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md).

---

## 1. Before you start

You need Python 3.10 or newer. Nothing else — no libraries to install,
no account, no internet connection.

Check that your copy is complete:

```
./jyotish --self-check
```

Ten checks should pass. If one fails, the message says which resource is
missing; the program is still safe to use for everything that does not
depend on it.

---

## 2. The quickest thing

```
./jyotish --app
```

This opens a small web interface on your own machine. Your browser will
show it at `http://127.0.0.1:8765`. Nothing is sent anywhere — the page
is served by the program running on your computer, and it stops when you
close the terminal.

Fill in the form and press Calculate. That is the whole workflow.

### If you prefer the command line

```
./jyotish --name "Ram Sharma" --dob 1990-06-15 --time 06:30 --place Delhi
```

---

## 3. Entering birth details

**Date** is `YYYY-MM-DD`. **Time** is a 24-hour clock: `06:30`, or
`06:30:45` if you know the seconds.

**Birth-time precision matters more than people expect.** If your
records say 10:35, the program does not assume 10:35:00. Tell it how
well the time is really known:

| Setting | Use it when |
|---|---|
| Exact to the second | A hospital record with seconds |
| Exact to the minute | The usual case — a time written down at the time |
| Approximate, within 5 minutes | "About half past ten" |
| Approximate, within 15 minutes | "Mid-morning" |
| Not known | Anything vaguer |

The program then tells you which conclusions survive that uncertainty
and which do not. A divisional chart that changes within your margin of
error is marked as such, beside the finding that rests on it. This is
not pedantry: the D60 chart of the worked example changes 39 seconds
after the recorded birth time.

**Place** is looked up in a built-in list of cities. If your birthplace
is not in it, the program says so and stops. It never substitutes a
nearby city — a chart cast for the wrong place is wrong in a way you
would not notice.

If your place is missing, give coordinates instead:

```
./jyotish --name "…" --dob 1990-06-15 --time 06:30 \
          --lat 28.6139 --lon 77.2090 --timezone Asia/Kolkata
```

---

## 4. Reading what comes back

### Charts

You can have either style:

```
./jyotish … --chart-style north_indian     # the default
./jyotish … --chart-style south_indian
```

They show the same placements. The difference is what stays still:

- **North Indian** — the houses are fixed on the page. House 1 is always
  the top diamond, and the number printed in each region is the **sign**.
- **South Indian** — the signs are fixed. Mesha is always the same cell,
  the number printed in each cell is the **house**, and the ascendant's
  cell is marked with a diagonal stroke.

Changing the style changes nothing about the calculation. The program
tests this directly: every graha, in every sign, in every house, must be
identical across both.

Markers beside a graha are printed, never colour alone:

```
R  retrograde        ^   exalted        mt  moolatrikona
c  combust           v   debilitated    sv  own sign
```

### Reports

```
./jyotish … --report chart.pdf                 a PDF
./jyotish … --report-html chart.html           a web page
./jyotish … --report-mode summary              about 9 pages
./jyotish … --report-mode detailed             about 32 pages (default)
./jyotish … --report-mode technical            about 33 pages, with sources
```

The three depths contain the **same findings**. They differ in how much
of the working is shown; a sentence that appears in two of them is the
same sentence.

### Hindi

```
./jyotish … --language hi --report chart.pdf
```

Hindi is complete: the findings, the headings, the tables and the
disclaimers. The first Hindi PDF in a session takes a few seconds while
the text shaper warms up; later ones are quick.

---

## 5. What the program will not tell you

This matters more than the feature list.

**It does not predict events.** It reports what a set of rules says
about a chart. Where those rules produce a time window, the window is
the interval in which the program's conditions hold — not a forecast
that anything happens in it.

**It gives no probabilities.** Activation and confidence are ordinal
bands: `BACKGROUND`, `ACTIVE`, `STRONGLY_ACTIVE`; `LOW`, `MEDIUM`,
`HIGH`. They describe how much evidence the rules found and how stable
the calculation is. No number in any report is a likelihood, and none can
be converted into one.

**It is sometimes silent.** Under the strict setting the program will
say nothing at all about a life area if the evidence does not reach its
bar. Silence there means the evidence did not qualify — not that nothing
is indicated.

**It offers no remedies**, no gemstones, no mantras, and no birth-time
rectification.

**It is not a validated account of any tradition.** Nothing in this
build carries the highest provenance status. See
[METHODOLOGY.md](METHODOLOGY.md).

---

## 6. Choosing a methodology

Most people should leave the defaults alone. If you want to change them,
each choice is offered with its default visible and the choice is
recorded with every chart you produce.

The one worth understanding is the **synthesis profile**:

| Profile | What it admits |
|---|---|
| `strict` | Only rules traced to a located text. Often silent. |
| `standard` | The default. Documented methodology plus located sources. |
| `experimental` | Also rules with no located witness. |

A report produced under `experimental` **says so**, in the document,
beside the findings.

```
./jyotish … --synthesis-profile strict
```

---

## 7. Saving and sharing

```
./jyotish … --save-consultation ram.json     save the birth details
./jyotish --open-consultation ram.json       open them again
```

A saved file holds **the input and the methodology, not the answer** —
about a kilobyte. Opening it recomputes the chart, so a saved
consultation stays correct when the program is updated rather than
preserving a stale result. If you want the computed chart stored too,
add `--save-cache`; the file becomes about two megabytes and the cache
is only ever a cache.

Files saved by earlier versions still open. If the format has changed,
the program says what it migrated and what it assumed.

To move several consultations between machines:

```
./jyotish … --export-consultations backup.json
./jyotish --import-consultations backup.json
```

---

## 8. Privacy

```
./jyotish --privacy
```

prints the full statement. In short:

- Nothing leaves your machine. Not during calculation, interpretation,
  chart drawing or report generation.
- Nothing is written unless you ask for it. Casting a chart writes no
  file.
- The web interface listens only on `127.0.0.1` — your own computer, not
  your network.
- There is no telemetry, no crash upload and no update check.

If the program hits an error it did not expect, it writes a diagnostic
file locally and prints where. That file contains the technical fault
and **no birth details**, and it is never sent anywhere.

---

## 9. When something goes wrong

Ordinary problems produce a sentence and a suggestion, not a stack
trace. If you want the technical detail:

```
./jyotish … --debug
```

Common cases:

| Message | What to do |
|---|---|
| Birth place could not be resolved | Use `--lat` and `--lon` |
| …is not one of the available values | Check spelling; the message lists the valid ones |
| This consultation was written under schema… | The file is from a newer version |
| …contains a script no face can draw | Use `--report-html` for that language |

---

## 10. Everything at a glance

```
./jyotish --help                      every option
./jyotish --self-check                is this copy complete
./jyotish --privacy                   what is stored, what leaves
./jyotish --list-conventions          divisional chart conventions
./jyotish --selftest                  ephemeris accuracy check
./jyotish … --benchmark               how long each stage takes
```

---

## 11. Where to read more

- [METHODOLOGY.md](METHODOLOGY.md) — the profiles, and what "sourced"
  means here
- [SOURCE_VALIDATION.md](SOURCE_VALIDATION.md) — every rule and the
  passage behind it
- [RELEASE_NOTES.md](RELEASE_NOTES.md) — what changed in this version
- [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) — how it is
  built
