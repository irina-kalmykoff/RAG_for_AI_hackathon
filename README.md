# RAG for AI hackathon: Marlow & Finch exercise

A 10–15 minute hands-on exercise showing why retrieval-augmented generation (RAG) beats direct prompting for financial analysis.

Participants ask a chatbot (ChatGPT, Copilot, Gemini; no account needed) about the 2025 results of a **fictional** company, Marlow & Finch Coffee Roasters NV, twice:

1. directly, with no documents: the model guesses or refuses;
2. with excerpts from the annual report, found with the page's built-in keyword search: the model answers correctly and cites its sources.

A trap question shows that a well-cited answer can still be wrong when retrieval misses the key page.

## Files

- `index.html`: the participant page (questions, report search, copy-ready prompts).
- `data/`: the report as CSV files (five financial tables in EUR thousand, plus all 14 text excerpts), linked from the participant page for download. UTF-8 with BOM so Excel shows € and accents correctly.
- `facilitator-mf25-key.html`: run sheet, answer key and debrief points. Not linked from the participant page; don't share its address with participants.

## Deploy

Static files only, with no build step. On Netlify: drag this folder onto app.netlify.com/drop, or connect this repository with an empty build command and `.` as the publish directory.
