# Using the Web of Science skills

A plain-language guide. No coding needed — you'll copy and paste a few lines.

---

## First, the one thing that matters most

**These skills only work on your own computer.** They cannot work from
Claude Code on the web (claude.ai/code).

Here's why. The skills work by driving a Chrome window and by talking to
Zotero. Both of those have to be on the *same machine* Claude is running on.
When you use Claude on the web, Claude runs on a rented computer in a data
centre somewhere — it has no Chrome with your library login, and no Zotero.
It cannot reach across the internet into your laptop.

So: install Claude Code on your laptop, and run it there. Everything below
is about doing that.

Your institutional Web of Science account has nothing to do with your Claude
account, and that's fine. They never meet. You log into Web of Science in a
browser window; Claude reads that already-logged-in window. **Claude never
sees, asks for, or stores your university username or password.**

---

## What you need

| | | |
|---|---|---|
| **Node.js** | Required | https://nodejs.org — click the big **LTS** button |
| **Claude Code** | Required | Installed with one command, see below |
| **Google Chrome** | Required | https://www.google.com/chrome/ |
| **A Web of Science login** | Required | Your university account |
| **Zotero desktop** | Optional | https://www.zotero.org/download/ — only for saving citations |

Zotero is genuinely optional. Searching, reading paper details, and
downloading PDFs all work without it. You only need it for `/wos-export zotero`.

---

## Setup, step by step

### Step 1 — Open a terminal

- **Windows:** press Start, type `powershell`, press Enter.
- **Mac:** press Cmd+Space, type `terminal`, press Enter.

A window with a blinking cursor appears. You type lines into it and press
Enter after each one. That's all a terminal is.

### Step 2 — Install Claude Code

Copy this line, paste it into the terminal, press Enter:

```
npm install -g @anthropic-ai/claude-code
```

If it complains that `npm` isn't found, Node.js isn't installed yet — go to
https://nodejs.org, click **LTS**, run the installer, then **close the
terminal and open a new one** and try again. (The new window matters; the old
one won't have picked up the change.)

### Step 3 — Download this project

```
git clone https://github.com/hoankhai1707-crypto/Robert.git
cd Robert
```

If `git` isn't found, install it from https://git-scm.com/downloads first.

From now on, this `Robert` folder is where you run everything. If you close
the terminal and come back later, you need to `cd` back into it first.

### Step 4 — Check everything is ready

**Mac:**
```
bash scripts/setup-wos.sh
```

**Windows:**
```
powershell -ExecutionPolicy Bypass -File scripts\setup-wos.ps1
```

This looks at your computer and prints a list. It changes nothing, so run it
as often as you like.

- `[ OK ]` — that part is fine
- `[MISS]` — needs fixing; the line underneath tells you how
- `[ ?? ]` on Zotero — fine to ignore unless you want citation export

Fix any `[MISS]` lines, then run it again until they're gone.

### Step 5 — Start Claude

```
claude
```

The first time, it asks permission to use a server called
**chrome-devtools**. Say yes. That's the piece that lets Claude drive Chrome.

### Step 6 — Log into Web of Science

Ask Claude:

```
Open Web of Science in the browser
```

A Chrome window opens. **Log in there, in that window**, with your
institutional account — the usual route through your university library.

This is the step people get wrong, so it's worth being precise: it has to be
*that* Chrome window, the one Claude just opened. If you're already logged
into Web of Science in your normal everyday Chrome, that doesn't count.
Claude can only see the window it controls.

Leave that window open and sitting on a Web of Science page. Now you're ready.

---

## Using it

Type these into Claude:

```
/wos-search deep learning
```

```
/wos-search value co-creation --edition SSCI --sort citations
```

```
/wos-paper-detail WOS:000295471900004
```

```
/wos-navigate-pages 2
```

```
/wos-download WOS:000295471900004
```

```
/wos-export zotero
```

You can also just talk normally instead of using the slash commands:

> Find me the 20 most cited SSCI papers about value co-creation since 2020,
> show me the abstracts, and save them all to Zotero.

Claude will chain the steps together itself.

### What each one does

| Command | What it does |
|---|---|
| `/wos-search` | Searches by topic, author, title, or DOI |
| `/wos-paper-detail` | Full record — abstract, impact factor, JCR quartile, citation counts |
| `/wos-navigate-pages` | Moves to another page of results |
| `/wos-download` | Fetches the PDF through the publisher |
| `/wos-export` | Saves citations to Zotero, RIS, BibTeX, or Excel |

### Useful search options

Add these to the end of a `/wos-search`:

- `--edition SSCI` — social sciences only (or `SCI` for sciences, `CPCI` for conferences)
- `--sort citations` — most cited first (or `date` for newest, `relevance`)
- `--db alldb` — search all databases, not just the Core Collection

---

## About Zotero

You said you weren't sure whether Zotero is running. Here's how to know for
certain: run the check script from Step 4. Line 6 of its output tells you
plainly — either it's answering on port 23119 or it isn't.

If it isn't and you want citation export:

1. Open the Zotero desktop app (install from https://www.zotero.org/download/
   if you don't have it).
2. Leave it open — running in the background is enough, you don't need to
   look at it.
3. Run the check script again. Line 6 should now say `[ OK ]`.

Zotero has to be open at the moment you run `/wos-export zotero`. If it's
closed, the export fails with "Zotero not running" and nothing is lost —
just open it and try again.

---

## When something goes wrong

**"Claude can't see Web of Science" / searches return nothing**
The Chrome window Claude controls isn't on a logged-in Web of Science page.
Redo Step 6. Remember it must be the window Claude opened.

**"Zotero not running"**
The Zotero desktop app is closed. Open it, then run the export again.

**The `claude` command isn't found**
Either Step 2 didn't finish, or you need a fresh terminal window. Close it,
open a new one, try again.

**Session expired after a while**
Institutional logins time out. Go back to the Chrome window Claude opened
and log in again. Nothing else needs redoing.

**Web of Science starts blocking or challenging the browser**
The upstream project documents optional Chrome settings that reduce this by
making the automated browser look more like an ordinary one. They are
deliberately **not** switched on here, because using them pushes against what
Web of Science's terms of use allow. Read those terms and decide for
yourself; if you want them enabled afterwards, ask and it can be added.

---

## Credits

Skills and agent from [cookjohn/wos-skills](https://github.com/cookjohn/wos-skills),
installed unmodified.
