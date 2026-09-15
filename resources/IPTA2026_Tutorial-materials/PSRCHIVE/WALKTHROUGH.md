# PSRCHIVE Hands-On Tutorial

Welcome! This is the **hands-on** PSRCHIVE session. In the lecture you saw
*what* a folded pulsar archive is and how PSRCHIVE thinks about the data.
Here you will actually drive the tools on real MeerKAT data and turn a pile
of observations into a set of pulse arrival times (TOAs) — the starting
point for pulsar timing.

The session has three parts:

1. **Part 1 — Real data (we do this together).** A guided walk through the
   core PSRCHIVE programs on a real MeerKAT pulsar, ending with a `.tim`
   file of TOAs. This is the part that matters: it is the actual workflow
   you would use on your own data. Follow along on your screen as we go.
2. **Part 2 — The hidden-picture archives (you do this yourself).** A set of
   archives in `archives/` each hide a picture. The picture only develops
   when you apply the *correct* PSRCHIVE operation — the same operations you
   just learned in Part 1. If the picture appears, you did it right. These
   are here for fun and for practice; do as many as you like.
3. **Part 3 — Bonus (optional).** Two Jupyter notebooks: one driving
   PSRCHIVE from Python, and one using PulsePortraiture for wideband
   timing. For people who want to go further.

There is a one-page **`CHEATSHEET.md`** in this folder — keep it open beside
you while you work.

---

## Before you start

Your PSRCHIVE environment should already be loaded on the machine you have
been given — i.e. typing `vap` or `pav` at a terminal should just work. If a
command is "not found", **ask an instructor** how to load the environment on
this machine; the command differs between setups and we'll tell you on the
day.

Quick check that you're ready:

```bash
which vap pav pam psradd pat      # should print paths, not "not found"
```

Everything in this tutorial lives in one folder (the one this file is in).
`cd` into it and have a look:

```bash
ls
# archives/  real_data/  WALKTHROUGH.md  CHEATSHEET.md
# psrchive_python.ipynb  pulseportraiture.ipynb
```

It's a good habit not to work directly on the original files. Make yourself
a working copy to play in:

```bash
mkdir -p ~/psrchive_work
cd ~/psrchive_work
cp -r /path/to/this/folder/archives .       # the hidden-picture archives
ln -s /path/to/this/folder/real_data .      # the real MeerKAT data (large; link, don't copy)
```

(Replace `/path/to/this/folder` with wherever this tutorial was unpacked.
Ask if you're not sure.)

### Plotting to screen vs to a file

PSRCHIVE's plotting tools (`pav`, `psrplot`, `pazi`, `paas`) draw with
PGPLOT. You can either:

- **Plot to a window** (needs graphics forwarding / a desktop):
  `pav -D file.ar` opens an interactive window.
- **Plot to a PNG file** (always works, even with no display):
  `pav -D -g profile.png/png file.ar` writes `profile.png`.

If windows don't appear, just add `-g name.png/png` to any plot command and
open the PNG afterwards. The two are otherwise identical. Throughout this
doc the commands plot to screen; add `-g name.png/png` if you need files.

### Getting unstuck

Every PSRCHIVE program prints its options with `-h`:

```bash
pav -h
pam -h
paz -h
pat -h
```

The full manuals are online at <https://psrchive.sourceforge.net/manuals/>.

---

# Part 1 — Real data: from observations to TOAs

We'll work with real MeerKAT observations of the millisecond pulsar
**J1903−7051**, in `real_data/J1903-7051/`. These have already been
cleaned, calibrated and folded for you — they are the kind of files that
come out of a real timing pipeline. Our job is to understand them and turn
them into TOAs.

```bash
ls real_data/
# J1903-7051/                  the timing dataset we build TOAs from
# J0437-4715_rfi_practice.ar   a raw observation for the RFI step (§1.4)

ls real_data/J1903-7051/
# data/        one fully-scrunched, full-Stokes profile per epoch
# data_16ch/   the same epochs, kept at 16 frequency channels
# J1903-7015.par   the pulsar's ephemeris (timing model)
```

> The lecture and the slides cover the theory behind these steps; it's fine
> if some of this feels familiar — repetition is good.

## 1.1 — Look at what you have (`vap`, `psredit`, `psrstat`)

Never run anything blind. First read the metadata. `vap` ("view archive
parameters") prints header fields. Pick any one observation:

```bash
cd real_data/J1903-7051/data
vap -c name,nbin,nchan,nsubint,npol,freq,bw J1903-7051_2019-03-15-*.ar
```

- **name** — the source (J1903−7051).
- **nbin** — phase bins across one pulse period (1024 here).
- **nchan** — frequency channels. These files are `1` (fully
  frequency-scrunched); the `data_16ch/` versions keep 16.
- **nsubint** — time sub-integrations (`1`; fully time-scrunched).
- **npol** — polarisations (`4` = full Stokes).
- **freq / bw** — band centre and width in MHz.

Run `vap` on **all** the epochs at once to see the time span you're working
with:

```bash
vap -c name,length,mjd *.ar | head
ls *.ar | wc -l        # how many observations?
```

`psredit` dumps the *full* header (everything `vap` can show, and more):

```bash
psredit J1903-7051_2019-03-15-*.ar | head -40
```

`psrstat` computes quantities *from the data* rather than the header — most
usefully the signal-to-noise ratio:

```bash
psrstat -c snr J1903-7051_2019-03-15-*.ar
```

> **Try it:** which of your epochs has the highest S/N? (`psrstat -c snr *.ar`)

## 1.2 — Plot a single observation (`pav`, `psrplot`)

The first thing to do with any archive is *look* at the pulse. `pav` is the
quick all-purpose plotter. `-D` gives the dedispersed, fully-scrunched
**profile** (flux vs pulse phase):

```bash
pav -D J1903-7051_2019-03-15-*.ar
```

You should see a sharp millisecond-pulsar profile. This is total intensity
(Stokes I). Because these archives are full-Stokes, we can also look at the
**polarisation**:

```bash
pav -S J1903-7051_2019-03-15-*.ar
```

`-S` overlays total intensity (black), linear polarisation L (red) and
circular V (blue), with the polarisation position angle in the top panel.
`psrplot` is the lower-level cousin of `pav` and gives you finer control.
Unlike `pav`, **`psrplot` will not guess a graphics device** — you must give
it one with `-D`: `-D /xs` for an X window, or `-D name.png/png` for a PNG
file. The same profile is:

```bash
psrplot -p flux -D /xs J1903-7051_2019-03-15-*.ar       # to screen
psrplot -p flux -D flux.png/png J1903-7051_2019-03-15-*.ar   # to a PNG
```

## 1.3 — Scrunching, dedispersion, rotating, zooming

The single-channel `data/` files are already fully scrunched, so to *see*
what scrunching does we'll use a 16-channel version. `pam` is the archive
**m**anipulator: it applies an operation and writes a new file.

Go to the 16-channel data and plot frequency vs phase:

```bash
cd ../data_16ch
pav -G J1903-7051_2019-03-15-*.16chTS.dly.ar
```

`-G` is a greyscale image of **frequency (y) vs pulse phase (x)**. Each row
is one channel's profile. Now dedisperse on the fly — `-d` shifts each
channel to undo the interstellar dispersion delay so the pulse lines up
vertically:

```bash
pav -dG J1903-7051_2019-03-15-*.16chTS.dly.ar
```

**Average over frequency** (frequency-scrunch) with `pam -F`. This collapses
all 16 channels into one, boosting S/N:

```bash
pam -F -e Fav J1903-7051_2019-03-15-*.16chTS.dly.ar   # writes a .Fav file
pav -D *.Fav
```

`-e Fav` sets the output file extension. The four scrunches you'll use most:

| Flag | Operation | Combines… |
|------|-----------|-----------|
| `pam -T` | time-scrunch (`tscrunch`)  | all sub-integrations |
| `pam -F` | frequency-scrunch (`fscrunch`) | all channels |
| `pam -p` | polarisation-scrunch (`pscrunch`) | all pols → total intensity |
| `pam -D` | dedisperse | (aligns channels in phase) |

They combine: `pam -DTFp` does all four at once.

Two more handy `pav` view options — rotate the pulse to centre it, and zoom
in on it:

```bash
pav -D -r 0.25 *.Fav             # rotate by 0.25 of a turn
pav -D -z 0.4,0.6 *.Fav          # zoom to phase 0.4–0.6
```

> **Optional — measure the DM.** `pdmp` searches for the dispersion measure
> that maximises S/N:
> ```bash
> pdmp -g /NULL J1903-7051_2019-03-15-*.16chTS.dly.ar
> ```
> Compare its "Best DM" to the `DM` line in `../J1903-7015.par`.

## 1.4 — Clean RFI (`pazi`, `paz`)

Real raw data is contaminated by **radio-frequency interference** (RFI):
satellites, mobile networks, radar, etc. The J1903 files above have already
been cleaned, so to practise *removing* RFI we've included a genuinely raw
MeerKAT observation of the very bright pulsar **J0437−4715**:
`real_data/J0437-4715_rfi_practice.ar` (8 sub-integrations, 1024 channels).

Move to the `real_data` folder (we were in `data_16ch`) and look at it in the
frequency–phase plane:

```bash
cd ../..                                  # now in real_data/
pav -dG J0437-4715_rfi_practice.ar
```

The bright vertical strip is the pulsar; the **horizontal streaks** are RFI
contaminating particular frequency channels. There are two normal ways to
remove it.

**Automatic — `paz -r`** (the common production approach). This runs a
median-smoothed-difference algorithm that finds and zeroes (zaps) outlier
channels for you:

```bash
paz -r -e zap J0437-4715_rfi_practice.ar    # writes J0437-4715_rfi_practice.zap
pav -dG J0437-4715_rfi_practice.zap         # compare to the raw plot
```

Compare before/after — a good chunk of channels should now be flagged. Other
useful automatic flags: `-L` "mows the lawn" (removes outliers within each
sub-integration), `-b` removes a variable baseline.

**Interactive — `pazi`** (when you want to flag things by eye). `pazi` opens
a clickable display where you can zap individual channels, sub-integrations,
or bins:

```bash
pazi J0437-4715_rfi_practice.ar
```

In `pazi`: click a channel/subint to zap it, press **`p`** to toggle the
plot view, **`s`** to save, **`q`** to quit (it writes a `.pazi` file).
(`pazi` needs a graphics display; if you don't have one, stick with
`paz -r`.)

> You'll get to apply this skill again — without the safety rails — at one of
> the hidden-picture stations in Part 2.

## 1.5 — Combine all epochs into one high-S/N profile (`psradd`)

A single observation of a faint pulsar is noisy. To build a good **template**
we add many epochs together. `psradd` combines archives:

```bash
cd J1903-7051/data                # back to the J1903 single-channel epochs
psradd -o grand.average.ar *.ar
pav -S grand.average.ar
```

`-o` names the output. `psradd` will refuse to combine archives with
different source names — a useful safety check. Look at how much cleaner the
summed profile is than a single epoch.

## 1.6 — Make a timing template

A template (also called a "standard", `.std`) is a clean, noise-free model
of the pulse shape. `pat` will match it against each observation to measure
a TOA. There are two common ways to make one.

**Option A — scrunch and smooth.** Collapse the grand average to a single
total-intensity profile, then smooth away the noise with `psrsmooth -W`
(wavelet smoothing):

```bash
pam -Tp grand.average.ar -e Tp        # tscrunch + pscrunch -> grand.average.Tp
psrsmooth -W grand.average.Tp         # -> grand.average.Tp.sm
pav -D grand.average.Tp.sm
```

The `.sm` file is your template. Always plot it to check it looks sensible.

**Option B — fit Gaussians interactively.** `paas -i` opens an interactive
window where you build the profile from Gaussian components:

```bash
paas -i grand.average.Tp
```

In the window: **left-click** to add/centre a component, drag to set its
width and height, press **`f`** to fit, **right-click** (or `esc`) to remove
a component, **`s`** to save (writes `paas.std`), **`q`** to quit.

## 1.7 — Generate TOAs (`pat`)

Now match the template to every observation. `pat` ("**p**ulse **a**rrival
**t**imes") cross-correlates each profile with the template and reports when
the pulse arrived:

```bash
pat -s grand.average.Tp.sm *.ar
```

Each row is one TOA. To save them in the format the timing program `tempo2`
expects, add `-f tempo2`, and redirect to a file:

```bash
pat -f tempo2 -s grand.average.Tp.sm *.ar > J1903-7051.tim
head J1903-7051.tim
```

The columns of a tempo2 TOA are: **filename**, **frequency (MHz)**,
**arrival time (MJD)**, **uncertainty (µs)**, **telescope**. The uncertainty
is the key number — it's how precisely each pulse was timed.

> **Try it:** make a *second* template using Option B (`paas`) and generate a
> second `.tim`. Which template gives smaller TOA uncertainties? The lesson:
> your timing precision is only as good as how well your template matches
> the data.

## 1.8 — What happens next (handoff to timing)

You now have `J1903-7051.tim` (the measurements) and `J1903-7015.par` (the
model). The next session feeds both to **tempo2** to fit the timing model
and look at residuals. Its first command looks like:

```bash
tempo2 -gr plk -f real_data/J1903-7051/J1903-7015.par J1903-7051.tim
```

That's the bridge from PSRCHIVE (turning data into TOAs) to timing (turning
TOAs into science). **You've done the PSRCHIVE half — that's the goal of this
session.**

### Practice / choose your own path

If you'd like to cement this, **do Part 1 again on your own** from §1.1 — try
the highest-S/N subset of epochs, or both template methods. If you're
comfortable and want something more playful, head to **Part 2**.

---

# Part 2 — The hidden-picture archives

Everything from here on is **yours to explore at your own pace.** The folder
`archives/` contains a set of archives, each with a deliberately
uninformative filename (`alpha.ar`, `beta.ar`, …). Hidden inside each one is
a **picture** — but it is scrambled exactly the way real pulsar data is
obscured (dispersion, polarisation mixing, RFI, low S/N). The picture only
**develops** when you apply the right PSRCHIVE operation, which is one of the
operations you used in Part 1.

**There's no answer key here on purpose.** You'll *know* you got it right,
because a recognisable picture will appear. If you see noise or a smear, the
operation wasn't right (or wasn't finished) yet. That's the whole game.

> The pictures are a surprise — don't peek at other people's screens if you
> want to find them yourself!

## Start here: get your map

Begin the way you began Part 1 — by inspecting the headers. From the tutorial
folder, go into `archives/` and read each file's SOURCE **codename**:

```bash
cd archives        # (from the tutorial root)
vap -c name *.ar herd/*.ar
```

Each file reports a cryptic codename — `J_STATION1`, `J_STATION2`, … (the
eight `herd/` files all share one). **The number tells you which station
below the file belongs to** — that's your only clue; the rest is up to you.
Pick a file, find its matching station, and develop the picture. (All the
commands below assume you're inside `archives/`.)

## The stations

Each "station" below names the **skill** and the **clue**, but not the
picture. Match the clue to the right command(s). All of these are things you
did in Part 1.

### Station 1 — *Develop with time*
**Clue:** "dedisperse, then average over time."
A picture is encoded across **frequency and phase**, shared by every
sub-integration. Dedisperse so the channels line up, and time-scrunch so the
noise averages down. Then view frequency vs phase.

*Tools you used in Part 1:* `pam -D`, `pam -T`, `pav -G`. Remember `pav` can
do several at once (`pav -GTd …`).

### Station 2 — *Develop with frequency*
**Clue:** "dedisperse, then average over frequency."
Same idea as Station 1, but this picture lives in the **time vs phase** plane
— so you average over *frequency* instead of time, and view time vs phase
(`pav -Y`).

### Station 1+2 — *Two for one*
**Clue:** "two pictures in one file."
One file hides **both** of the above. One picture develops when you average
over time; the other when you average over frequency. See if you can pull out
each one in turn from the same archive.

### Station 3 — *Develop with polarisation*
**Clue:** "convert to Stokes and look at the right polarisation."
This picture is hidden in a **single polarisation**. A normal greyscale
won't show it, because the archive is stored in the instrument's native
(coherency) basis. Convert the state to Stokes first (`pam -S`, or combine it
with the scrunches: `pam -DTS`), then plot the polarisation you want. To plot
one specific Stokes parameter as an image, `psrplot` is your friend:

```bash
psrplot -p freq -c "pol=3" file.ar    # pol 0,1,2,3 = I,Q,U,V once in Stokes
```

There may be more than one way to reveal something here — a 2D image *and*
something in the polarisation **profile** (`pav -SFT`). Worth exploring.

### Station 4 — *Clean, then develop*
**Clue:** "RFI is burying the picture."
The picture is in frequency vs phase (like Station 1), but bright **RFI
bands** and a **burst across a few sub-integrations** dominate the plot and
hide it. First *see* the mess (`pav -GTd`), then flag the offending channels
and subints, and develop the cleaned file.

This is the skill you practised on the J0437 data in §1.4 — but here the
contamination is deliberate and sharp-edged, so it rewards a **visual**
approach. Open it in the interactive zapper and remove what you can see:

```bash
pazi epsilon.ar      # (or whichever file is J_STATION4) — zap the bands/subints by eye
```

(The automatic `paz -r` is tuned for natural RFI and may *not* catch these
injected bands — try it and see.) If you have no graphics display, read the
band edges and bad-subint range off the `pav -GTd` plot and pass them to
`paz` non-interactively instead: `paz -F "lo hi"` zaps a frequency range in
MHz (repeatable), `paz -W "lo hi"` zaps a sub-integration range, `-e zap`
sets the output extension.

### Station 5 — *Develop from many*
**Clue:** "one plate of eight — add them all together."
There are eight archives in `herd/`. Any single one looks like a
cluttered mess. But they were built so that adding **all eight** together
makes the clutter cancel out and leaves a single clean picture standing
(this is a real trick — it's how spread-spectrum codes and matched filtering
work). Combine them with `psradd`, then develop as usual.

```bash
psradd -o sum.ar herd/herd_*.ar
# ... then the usual dedisperse + scrunch + view
```

Try summing only *some* of them and see why you need the whole set.

### Station 6 — *The full toolkit*
**Clue:** "three pictures: a polarisation profile, a frequency-phase plate,
and a timing template."
This one rewards everything you've learned. There are **three** different
things to find in the same archive:
- one in the **polarisation profile** (`pav -SFT`),
- one in the **frequency vs phase** plane (`pav -GTd`),
- and a **profile you can turn into a timing template** — scrunch it down
  (`pam -DTFp`), smooth it (`psrsmooth -W`), and you could even run `pat`
  against the real J1903 data with it (see what it does to the TOA
  uncertainties, and why).

---

# Part 3 — Bonus notebooks (optional)

Two Jupyter notebooks ship with this tutorial. Launch Jupyter from a
terminal with the PSRCHIVE environment loaded:

```bash
jupyter notebook        # or: jupyter lab
```

### `psrchive_python.ipynb` — PSRCHIVE from Python

Everything the command-line tools do, the `psrchive` Python package can do
too — and you can mix it with numpy/matplotlib for custom analysis and
plotting. The notebook tours loading archives, reading the header and data
cube, scrunching/dedispersing/state-converting, accessing per-channel and
per-subint data, and making your own plots. It uses both the real J1903 data
and the hidden-picture archives as examples.

### `pulseportraiture.ipynb` — Wideband timing with PulsePortraiture

A more advanced bonus, mostly for those who already know PSRCHIVE well.
PulsePortraiture models how a pulse profile **changes with frequency** and
measures a TOA *and* a DM from each wideband observation simultaneously. The
notebook builds a frequency-resolved template from the real J1903 data and
generates wideband TOAs.

> **Note:** PulsePortraiture needs its own software environment, which may or
> may not be set up on the machine you're using. If the first `import` cell
> fails, that environment isn't available here — that's expected; this is a
> stretch goal.

---

# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `command not found` | PSRCHIVE environment not loaded | Ask an instructor how to load it on this machine. |
| Plot window never appears | No graphics forwarding | Plot to a file instead: add `-g name.png/png` to the command. |
| A picture looks like pure noise / a smear | Operation not finished (e.g. forgot to dedisperse, or didn't scrunch the right axis) | Re-read the station clue; check you dedispersed (`-d`/`pam -D`). |
| `pav -S` says "incomplete polarization information" | The file was pscrunched (`-p`) to one polarisation | Use a file that still has 4 polarisations. |
| `psrplot -c "pol=3"` "out of range" | Archive is still in the native (coherency) state | Convert first: `pam -S` (or `pam -DTS`). |
| `psradd` "source name mismatch" | The files have different `name` headers | `psradd` only combines matching sources; check `vap -c name`. |
| `pav` writes `out.png_2` not `out.png` | PGPLOT won't overwrite an existing file | `rm out.png` first, or use a new filename. |
| `FITSArchive::load_Pointing correcting …` messages | Harmless header coordinate fix-ups | Ignore them. |

---

# Cheat sheet (summary)

A fuller one-pager is in `CHEATSHEET.md`. The essentials:

| Want to… | Command |
|---|---|
| Read header fields | `vap -c name,nbin,nchan,nsubint,npol,freq,bw file.ar` |
| Dump full header | `psredit file.ar` |
| Measure S/N | `psrstat -c snr file.ar` |
| Plot profile | `pav -D file.ar` |
| Plot polarisation profile | `pav -S file.ar` |
| Greyscale freq vs phase | `pav -G file.ar` (add `-d` to dedisperse) |
| Greyscale time vs phase | `pav -Y file.ar` |
| Rotate / zoom a plot | `pav -D -r 0.25 file.ar` / `pav -D -z 0.4,0.6 file.ar` |
| Dedisperse / T / F / P scrunch | `pam -D` / `-T` / `-F` / `-p` (combine: `-DTFp`) |
| Convert to Stokes | `pam -S file.ar` |
| Plot one Stokes pol as image | `psrplot -p freq -c "pol=3" -D /xs file.ar` (psrplot needs `-D`) |
| Auto-zap RFI | `paz -r -e zap file.ar` |
| Zap RFI band / subints by hand | `paz -F "lo hi" -W "lo hi" -e zap file.ar` |
| Interactive zapper | `pazi file.ar` |
| Combine archives | `psradd -o out.ar files*.ar` |
| Smooth a template | `psrsmooth -W file.ar` → `file.sm` |
| Interactive Gaussian template | `paas -i file.ar` |
| Generate TOAs | `pat -f tempo2 -s template.sm obs*.ar > out.tim` |
| Set output extension | add `-e EXT` to `pam`/`paz` |
| Help for any tool | `<tool> -h` |
