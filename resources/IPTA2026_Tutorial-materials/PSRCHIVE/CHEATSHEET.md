# PSRCHIVE Cheat Sheet

Keep this open while you work. `<tool> -h` prints options for any tool.
Manuals: <https://psrchive.sourceforge.net/manuals/>

## Inspect (read before you process)
| Task | Command |
|---|---|
| Header field(s) | `vap -c name,nbin,nchan,nsubint,npol,freq,bw,dm file.ar` |
| One field, many files | `vap -c snr *.ar` |
| Full header | `psredit file.ar` |
| One header field | `psredit -c comment file.ar` |
| S/N (from data) | `psrstat -c snr file.ar` |
| Best-fit DM search | `pdmp -g /NULL file.ar` |

## Plot (`pav` = quick, `psrplot` = fine control)
| Task | Command |
|---|---|
| Profile (flux vs phase) | `pav -D file.ar` |
| Polarisation profile (I, L, V + PA) | `pav -S file.ar` |
| Freq vs phase (greyscale) | `pav -G file.ar` |
| Time vs phase (greyscale) | `pav -Y file.ar` |
| Dedisperse on the fly | add `-d` (e.g. `pav -dG file.ar`) |
| Combine view + scrunch | `pav -GTd file.ar` (greyscale, T-scrunch, dedisp) |
| Rotate pulse | `pav -D -r 0.25 file.ar` (turns) |
| Zoom phase range | `pav -D -z 0.4,0.6 file.ar` |
| One Stokes pol as image | `psrplot -p freq -c "pol=3" -D /xs file.ar` |
| Plot to a PNG (no display) | `pav`: add `-g name.png/png` · `psrplot`: `-D name.png/png` |

`pol=0,1,2,3` → `I,Q,U,V` **once the archive is in the Stokes state.**
**`psrplot` always needs a device:** `-D /xs` (window) or `-D name.png/png` (file).
`pav` defaults to a window; use `-g name.png/png` for a file.

## Manipulate (`pam` writes a new file; `-e EXT` sets the extension)
| Task | Command |
|---|---|
| Dedisperse | `pam -D file.ar` |
| Time-scrunch (sum subints) | `pam -T file.ar` |
| Freq-scrunch (sum channels) | `pam -F file.ar` |
| Pol-scrunch (→ total intensity) | `pam -p file.ar` |
| All of the above | `pam -DTFp file.ar` |
| Convert to Stokes | `pam -S file.ar` |
| Rotate by phase | `pam -r 0.25 file.ar` |
| Name the output extension | `pam -T -e timeAv file.ar` → `file.timeAv` |

## Clean RFI (`paz`, `pazi`)
| Task | Command |
|---|---|
| **Automatic** (median-difference) | `paz -r -e zap file.ar` |
| Mow the lawn / remove baseline | `paz -L file.ar` / `paz -b file.ar` |
| Zap a frequency band (MHz) | `paz -F "1100 1130" -e zap file.ar` |
| Zap several bands | `paz -F "1100 1130" -F "1400 1430" -e zap file.ar` |
| Zap sub-integration range | `paz -W "30 34" -e zap file.ar` |
| Interactive zapper (by eye) | `pazi file.ar` |

## Combine & template & TOAs
| Task | Command |
|---|---|
| Add archives (must share `name`) | `psradd -o grand.average.ar *.ar` |
| Make a profile to smooth | `pam -Tp grand.average.ar -e Tp` |
| Smooth into a template | `psrsmooth -W grand.average.Tp` → `…Tp.sm` |
| Interactive Gaussian template | `paas -i file.ar` (saves `paas.std`) |
| Generate TOAs (tempo2 format) | `pat -f tempo2 -s template.sm *.ar > psr.tim` |

TOA columns: **filename  freq(MHz)  MJD  uncertainty(µs)  telescope**

## `paas -i` keys
left-click = add/centre component · drag = width/height · `f` = fit ·
right-click/`esc` = remove · `s` = save (`paas.std`) · `q` = quit

## The usual "reveal" pipeline
```bash
pam -D file.ar -e D      # 1. dedisperse
pam -T file.D -e DT      # 2. scrunch the axis you don't want
pav -G file.DT           # 3. view  (or do it all at once: pav -GTd file.ar)
```
