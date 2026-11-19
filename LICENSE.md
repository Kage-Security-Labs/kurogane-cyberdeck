# Licensing

Kurogane K-7 uses a different license for each kind of file.

| What | Paths | License | SPDX |
|------|-------|---------|------|
| Hardware design files | `hardware/`, `enclosure/`, `bom/` | CERN Open Hardware Licence v2, Strongly Reciprocal | `CERN-OHL-S-2.0` |
| Software and tools | `software/`, `tools/` | MIT License | `MIT` |
| Documentation and renders | `docs/`, `mockup/`, `README.md` | Creative Commons Attribution-ShareAlike 4.0 | `CC-BY-SA-4.0` |

Full texts:

- `LICENSES/MIT.txt` (included)
- CERN-OHL-S-2.0: https://ohwr.org/cern_ohl_s_v2.txt
- CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt

Before the first public release, download the two linked texts into `LICENSES/` as
`CERN-OHL-S-2.0.txt` and `CC-BY-SA-4.0.txt`:

```
curl -L -o LICENSES/CERN-OHL-S-2.0.txt https://ohwr.org/cern_ohl_s_v2.txt
curl -L -o LICENSES/CC-BY-SA-4.0.txt   https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt
```

Want something more permissive? Swap CERN-OHL-S for CERN-OHL-P (hardware) and CC BY-SA for CC BY
(docs) before you publish; changing licenses later needs every contributor's agreement.

Third-party material: KiCad footprints or symbols copied from the Raspberry Pi CM5 IO Board design
files keep Raspberry Pi Ltd's terms. Product names belong to their owners.
