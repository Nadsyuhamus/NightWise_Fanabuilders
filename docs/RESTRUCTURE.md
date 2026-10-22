# Repository structure repair

Based on commit 493c933. Core implementation lives in nightwise/, configuration
in config/, module entry points in scripts/, tests in tests/, and generated
results in root outputs/. Duplicate script/configuration/output copies removed.

nightwise/paths.py anchors filesystem locations to the project root. The core
scenario runner lives in nightwise/runner.py; scripts/run_simulation.py delegates
to it. The exporter implementation is scripts/export_results.py.

Default unittest discovery works through tests/__init__.py. Dashboard and
controller tests reference the real root app and configuration directory.
Provenance hashes include nested source/test/configuration paths without filename
collisions. Existing simulation policy and modelling assumptions are unchanged.

Verification: 64 tests passed, including rendered energy values for seven dashboard
scenarios, export integrity and nested-source hashing. All three demo commands
and the one-pedestrian scenario command completed. See logs/restructure_test_results.txt.

Run from the project root:

```bash
python -m unittest discover -v
python -m scripts.run_simulation --scenario one_pedestrian
python -m scripts.export_results --scenario all
python -m streamlit run app.py
```

After a source commit, regenerated scenario metadata identifies that source
commit. An artifact commit may follow; preserve the recorded source identity.
