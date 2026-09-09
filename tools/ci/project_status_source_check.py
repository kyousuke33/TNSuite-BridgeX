#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PIN=ROOT/'contracts/project-status.lock.json'; CONFIG=ROOT/'contracts/project-status.producer.json'; GEN=ROOT/'tools/project_status/generate.py'
EXPECTED_PIN={"schema":"tnsuite.project-status-family-pin.v1","contract_source":"kyousuke33/TNSuite-Platform-Contracts","contract_ref":"b12c68c43c8f3a4883da295b189173d562b981fa","contract_id":"tnsuite.project-status.v1","contract_version":"1.0.1","compatibility":">=1.0.0,<2.0.0","generated_payload_path":".project-status/status.json","family_pin_model":"affected-scope-exact-git-sha","portal_sso_repin_required":False,"deephealth_repin_required":False}
SECRET=re.compile(r"secret|token|password|authorization|cookie|session|private_key|credential|actor_assertion",re.I)
PRIV=re.compile(r"/(?:var/www|etc|root|home|opt/tnsuite-ci|run/tnsuite|var/lib/tnsuite)",re.I)
TOP={"schema","project_key","producer","source","status","milestone","current_work","progress","blockers","readiness","links","updated_at","freshness","provenance"}

def fail(x): raise SystemExit(f"PROJECT_STATUS_SOURCE_CHECK=FAIL reason={x}")
def git(*a): return subprocess.check_output(["git","-C",str(ROOT),*a],text=True).strip()
def walk(v):
    if isinstance(v,dict):
        for k,c in v.items(): yield k,c; yield from walk(c)
    elif isinstance(v,list):
        for c in v: yield from walk(c)

def main():
    try: pin=json.loads(PIN.read_text()); cfg=json.loads(CONFIG.read_text())
    except Exception as e: fail(f"CONFIG_PARSE:{e}")
    if pin != EXPECTED_PIN: fail("PROJECT_STATUS_FAMILY_PIN_MISMATCH")
    if cfg.get("schema") != "tnsuite.project-status-producer-config.v1": fail("PRODUCER_CONFIG_SCHEMA")
    for e in cfg.get("authority_evidence",[]):
        p=ROOT/str(e.get("path","")); marker=str(e.get("contains",""))
        if not p.is_file() or not marker or marker not in p.read_text(encoding="utf-8"): fail(f"AUTHORITY_EVIDENCE_MISSING:{e}")
    head=git("rev-parse","HEAD")
    with tempfile.TemporaryDirectory(prefix="project-status-source-") as tmp:
        paths=[Path(tmp)/"one.json",Path(tmp)/"two.json"]
        for out in paths:
            p=subprocess.run(["python3",str(GEN),"--source-sha",head,"--branch","main","--output",str(out)],text=True,capture_output=True)
            if p.returncode: fail("GENERATOR_EXECUTION:"+(p.stderr.strip() or p.stdout.strip()))
        if paths[0].read_bytes()!=paths[1].read_bytes(): fail("GENERATOR_NONDETERMINISTIC")
        payload=json.loads(paths[0].read_text())
    if set(payload)!=TOP: fail("PAYLOAD_TOP_LEVEL_SHAPE")
    if payload.get("schema")!="tnsuite.project-status.v1" or payload.get("project_key")!=cfg.get("project_key"): fail("PAYLOAD_IDENTITY")
    repo=cfg.get("repository"); source=payload.get("source") or {}; prov=payload.get("provenance") or {}
    if payload.get("producer")!={"repository":repo,"kind":"project-repository"}: fail("PAYLOAD_PRODUCER")
    if source!={"repository":repo,"branch":"main","sha":head} or prov.get("source_sha")!=head: fail("PAYLOAD_SOURCE_BINDING")
    if payload.get("status")!=cfg.get("declared_status") or payload.get("status") not in {"REPORTED","BLOCKED"}: fail("PAYLOAD_STATUS")
    if payload.get("milestone")!=cfg.get("milestone") or payload.get("current_work")!=cfg.get("current_work"): fail("PAYLOAD_PRODUCT_TRUTH")
    if payload.get("blockers")!=cfg.get("blockers",[]): fail("PAYLOAD_BLOCKERS")
    if payload.get("status")=="BLOCKED" and not payload.get("blockers"): fail("BLOCKED_REQUIRES_BLOCKER")
    if payload.get("progress")!={"status":"NOT_REPORTED","completed_units":None,"planned_units":None,"percent":None,"denominator_ref":None}: fail("PAYLOAD_PROGRESS_OVERCLAIM")
    if payload.get("readiness")!={"qa":"NOT_VERIFIED","security":"NOT_VERIFIED","release":"NOT_VERIFIED"}: fail("PAYLOAD_READINESS_OVERCLAIM")
    if (payload.get("freshness") or {}).get("stale_after_seconds")!=86400: fail("PAYLOAD_FRESHNESS")
    for k,c in walk(payload):
        if SECRET.search(str(k)): fail("SECRET_LIKE_FIELD")
        if isinstance(c,str) and PRIV.search(c): fail("PRIVILEGED_PATH_LEAK")
    print("PROJECT_STATUS_FAMILY_PIN=PASS"); print("PROJECT_STATUS_AUTHORITY_EVIDENCE=PASS"); print("PROJECT_STATUS_SOURCE_PAYLOAD_DETERMINISM=PASS"); print("PROJECT_STATUS_PROGRESS_AUTHORITY=NOT_REPORTED_NO_GOVERNED_DENOMINATOR"); print("PROJECT_STATUS_READINESS_INFERENCE=NONE"); print("PROJECT_STATUS_SOURCE_CHECK=PASS")
    return 0
if __name__=="__main__": raise SystemExit(main())
