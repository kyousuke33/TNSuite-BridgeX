# Decisions
- GitHub `main` becomes canonical source only after exact Hotfix16 bootstrap import/PR merge.
- Hotfix16 is the accepted baseline; Build13 is the next feature build.
- Desktop runtime uses Windows launch/GUI/transfer acceptance, not web health.
- Generated BuildKit audit/evidence files are not canonical source.
- Active historical-named regression scripts are retained until a separately rebuilt semantic-QA refactor.
- Optional auto-update is mediated by RCP/Portal; client does not trust GitHub directly.
