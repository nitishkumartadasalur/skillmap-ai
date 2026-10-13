# SkillMap AI: Resume Matcher and Skill Gap Analyzer

A Streamlit app that compares one resume against several job descriptions. It ranks the jobs, shows which skills match and which are missing, and suggests honest improvements to the resume. It uses TF-IDF and cosine similarity (scikit-learn), Pandas, and Plotly, with a dark navy and indigo interface.

## Quick start (VS Code)

1. Unzip the project and open the `skillmap-ai` folder in VS Code (**File > Open Folder**).
2. Open a terminal in VS Code (**Terminal > New Terminal**) and run:

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

   **Windows (PowerShell)**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python -m streamlit run app.py
   ```

   `run.sh` (macOS/Linux) and `run.bat` (Windows) do the same steps in one go.
3. The app opens at <http://localhost:8501>. Open **Setup**, choose **Use a sample** for the resume, select **Load sample jobs**, then **Analyze match**.

To run or debug from VS Code instead, pick **SkillMap AI (Streamlit)** in the Run and Debug panel (`.vscode/launch.json`).

### Python 3.14 compatibility

The project targets Python 3.14.0 and uses nothing that was removed or changed in 3.14. Whether `pip` can install everything on 3.14 depends on which wheels the packages publish, and **I could not check that here**: the build environment had Python 3.12 and no network access.

- `requirements.txt` uses **lower bounds, not pins** (for example `numpy>=2.3.2`, `pandas>=2.3.3`, `scikit-learn>=1.7.2`). Those are the first releases I believe ship Python 3.14 wheels. Streamlit pulls in `pyarrow` and `pillow`, and python-docx pulls in `lxml`, which also need 3.14 wheels. This is from my knowledge of those projects, not from an install I ran.
- If `pip install` fails on 3.14 (a package without a wheel tries to compile from source), the reliable fix is Python 3.13: `py -3.13 -m venv .venv` on Windows, or `python3.13 -m venv .venv` elsewhere. Nothing in the code needs 3.14.
- Streamlit versions before 1.50 may not accept `width="stretch"` on charts and tables. The app catches that and falls back to the older argument, but I recommend keeping Streamlit current.

## What it does

| Tab | What you get |
| --- | --- |
| **Setup** | Upload a resume (PDF, DOCX, TXT), paste text, or use a sample. Add any number of job descriptions, or load five samples. Skills found in your resume are previewed immediately. |
| **Rankings** | Best match highlighted, summary figures, a ranked bar chart, a table, and a chart of what drives each score. |
| **Skill gap** | Pick a job to see matched skills, missing required skills, and missing preferred skills, plus a gauge, a coverage radar by skill area, and a donut. A heatmap shows every skill against every job, and a bar chart shows your most common gaps. |
| **Improve resume** | Prioritised suggestions for the selected job, plus general resume checks. |
| **Export** | Three CSV downloads: ranking, skill gap detail, and suggestions. |

## How scoring works

- **Text similarity** is the cosine similarity between TF-IDF vectors of the resume and each job description. The vectoriser is fitted on the resume and all jobs together, using unigrams and bigrams, sublinear term frequency, and an English stop-word list extended with job-post boilerplate. Symbol-heavy skills (`C++`, `C#`, `.NET`, `CI/CD`, `Node.js`) are protected before tokenising.
- **Skill coverage** is the share of the job's recognised skills that appear on the resume. Skills the posting marks as *required* count 1.0, and skills under "Nice to have", "Preferred", "Bonus", or phrased as "is a plus" count 0.5.
- **Overall match** = `(1 - w) x text similarity + w x skill coverage`, where `w` is the sidebar slider (default 60%). Set it to 0% for pure TF-IDF cosine similarity.
- Jobs are ranked by overall match, best first. If a posting contains no recognised skills, its overall score falls back to text similarity alone, and the app says so.

Raw TF-IDF cosine similarity between a resume and a job post is usually low (often 10 to 40%) even for good fits, because the two documents use different vocabulary. The app does not rescale it to look better. Use it to compare jobs with each other, and treat skill coverage as the easier number to read on its own.

## Resume suggestions never invent experience

The suggestions are rule-based and written to be conditional:

- Every skill-gap suggestion says to add the skill **only if you have genuinely used it**, and otherwise to leave it off. Transferable experience is described as overlap, not as the missing skill.
- The app never generates resume bullets, employers, dates, metrics, or qualifications.
- General checks cover structure (summary, skills, experience), length, bullets without measurable results, and passive phrasing. For missing numbers, it says to use real figures or describe scope in plain words rather than estimate.
- A test (`tests/test_suggestions.py`) fails if skill-gap advice becomes unconditional.

## Project layout

```
skillmap-ai/
├── app.py                    Streamlit UI (tabs, state, wiring)
├── skillmap/
│   ├── skills_db.py          Skill taxonomy: ~250 skills, aliases, categories, skill groups
│   ├── parsing.py            PDF / DOCX / TXT text extraction and error handling
│   ├── extraction.py         Skill extraction, required vs preferred detection
│   ├── matching.py           TF-IDF cosine similarity, skill coverage, score blending
│   ├── analysis.py           Orchestration and the DataFrames used by charts and CSVs
│   ├── suggestions.py        Honest, rule-based resume suggestions
│   ├── charts.py             Plotly figures (navy / indigo theme)
│   ├── ui.py                 CSS and HTML components
│   └── samples.py            Loads the bundled sample data
├── data/
│   ├── sample_resumes/       3 fictional resumes (.txt)
│   │   └── upload_examples/  The same content as .pdf and .docx for testing uploads
│   └── sample_jobs/          5 fictional job descriptions
├── tests/                    60 tests (unittest-style, run with pytest)
├── scripts/make_sample_files.py
├── .streamlit/config.toml    Dark navy / indigo theme
├── .vscode/                  Launch and test settings
├── requirements.txt          Runtime dependencies
└── requirements-dev.txt      Adds pytest and reportlab
```

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Without pytest, `python -m unittest discover -s tests -t .` runs the same tests.

## What has and hasn't been verified

Verified in the build environment (Python 3.12.3, scikit-learn 1.8.0, pandas 3.0.2, numpy 2.4.4, pypdf 5.9.0, python-docx 1.2.0):

- All core logic: parsing, skill extraction, TF-IDF matching, scoring, analysis tables, suggestions, and CSV output. The 58 tests that cover them pass.
- `app.py` was run end to end against a **stand-in Streamlit and Plotly**, simulating a full session: loading a sample resume and jobs, analysing, moving the slider, switching jobs, adding, removing and clearing jobs, and exporting. That checks the control flow and data handling, not what the page looks like.

**Not verified** (Streamlit and Plotly could not be installed without network access):

- The real rendered appearance, including the CSS theme, charts, and layout. Streamlit changes its internal HTML between versions, so a few cosmetic CSS selectors may need small tweaks.
- Whether Plotly accepts every figure option on your installed version. The chart code follows the documented API, but it has not been run against Plotly.
- `tests/test_app_smoke.py`, which drives the real app with Streamlit's `AppTest`. It skips itself when Streamlit is missing, so it has never run. It is the first thing to run on your machine; if it fails, the traceback should point at a real issue.

If something looks wrong on first launch, please check those three areas first.

## Limitations

- Skills come from a built-in list, so technologies outside it are not detected. Add your own in `skillmap/skills_db.py` as `"Canonical|alias|alias"` lines inside a category.
- A few ambiguous names (`R`, `Go`, `C`, `Swift`, `Excel`) are only counted when they appear in a list or end a line or sentence, to avoid matching ordinary words. A resume that mentions "C" only inside a sentence may be missed.
- Scanned (image-only) PDFs have no text to read, and OCR is not included. Legacy `.doc` files are not supported; save them as `.docx`.
- Resume layout (columns, text boxes) can scramble the order of text extracted from a PDF. This does not affect skill detection much, but it can affect the text similarity.
- It is a screening aid. It does not know your seniority, the employer's real priorities, or experience that your resume doesn't state.

## Privacy

The app runs on your machine. Uploaded files are processed in memory and not written to disk by the app, and no resume text is sent to an external service. The only outside request is the browser fetching the Plus Jakarta Sans web font from Google Fonts. If that is blocked, the interface falls back to a system font.

## Sample data

All names, companies, and resumes in `data/` are fictional.
