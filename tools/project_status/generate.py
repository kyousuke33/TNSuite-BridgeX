#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "contracts/project-status.producer.json"
SCHEMA = "tnsuite.project-status.v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

class GenerationError(RuntimeError): pass

def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git","-C",str(ROOT),*args],text=True,stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError as exc:
        raise GenerationError(exc.output.strip() or "git command failed") from exc

def commit_time(sha: str) -> str:
    raw=git("show","-s","--format=%cI",sha)
    dt=datetime.fromisoformat(raw.replace("Z","+00:00"))
    if dt.tzinfo is None: raise GenerationError("SOURCE_COMMIT_TIMESTAMP_NAIVE")
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def load_config() -> dict:
    data=json.loads(CONFIG.read_text(encoding="utf-8"))
    if data.get("schema") != "tnsuite.project-status-producer-config.v1": raise GenerationError("CONFIG_SCHEMA_INVALID")
    for evidence in data.get("authority_evidence",[]):
        path=ROOT / str(evidence.get("path", ""))
        marker=str(evidence.get("contains", ""))
        if not path.is_file() or not marker or marker not in path.read_text(encoding="utf-8"):
            raise GenerationError(f"AUTHORITY_EVIDENCE_MISSING:{evidence}")
    return data

def build(source_sha: str, branch: str, ttl: int) -> dict:
    if not SHA40.fullmatch(source_sha): raise GenerationError("SOURCE_SHA_INVALID")
    if branch != "main": raise GenerationError("CANONICAL_BRANCH_MUST_BE_MAIN")
    if not 60 <= ttl <= 604800: raise GenerationError("FRESHNESS_TTL_OUT_OF_RANGE")
    if git("rev-parse","HEAD") != source_sha: raise GenerationError("CHECKOUT_SOURCE_SHA_MISMATCH")
    cfg=load_config(); repo=cfg["repository"]; key=cfg["project_key"]; status=cfg["declared_status"]
    blockers=cfg.get("blockers",[])
    if status not in {"REPORTED","BLOCKED"}: raise GenerationError("REAL_PRODUCER_STATUS_INVALID")
    if status == "BLOCKED" and not blockers: raise GenerationError("BLOCKED_REQUIRES_BLOCKER")
    return {
      "schema":SCHEMA,
      "project_key":key,
      "producer":{"repository":repo,"kind":"project-repository"},
      "source":{"repository":repo,"branch":branch,"sha":source_sha},
      "status":status,
      "milestone":cfg.get("milestone"),
      "current_work":cfg.get("current_work"),
      "progress":{"status":"NOT_REPORTED","completed_units":None,"planned_units":None,"percent":None,"denominator_ref":None},
      "blockers":blockers,
      "readiness":{"qa":"NOT_VERIFIED","security":"NOT_VERIFIED","release":"NOT_VERIFIED"},
      "links":[
        {"kind":"document","label":f"{key} Roadmap","url":f"https://github.com/{repo}/blob/main/docs/00_PRODUCT/ROADMAP.md"},
        {"kind":"document","label":f"{key} Current State","url":f"https://github.com/{repo}/blob/main/docs/90_GOVERNANCE/CURRENT_STATE.md"},
      ],
      "updated_at":commit_time(source_sha),
      "freshness":{"stale_after_seconds":ttl},
      "provenance":{"source_sha":source_sha,"generator":f"{key}-project-status-generator/1"},
    }

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--source-sha",required=True); p.add_argument("--branch",default="main"); p.add_argument("--output",default=".project-status/status.json"); p.add_argument("--stale-after-seconds",type=int,default=86400)
    a=p.parse_args()
    try:
        payload=build(a.source_sha.strip().lower(),a.branch.strip(),a.stale_after_seconds)
        out=Path(a.output); out=out if out.is_absolute() else ROOT/out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding="utf-8")
    except Exception as exc:
        print(f"PROJECT_STATUS_GENERATOR=FAIL reason={exc}",file=sys.stderr); return 2
    print("PROJECT_STATUS_GENERATOR=PASS"); print(f"PROJECT_KEY={payload['project_key']}"); print(f"SOURCE_SHA={payload['source']['sha']}"); print(f"DECLARED_STATUS={payload['status']}"); print("PROGRESS=NOT_REPORTED"); return 0
if __name__ == "__main__": raise SystemExit(main())
