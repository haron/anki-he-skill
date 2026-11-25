---
name: hebrew-anki
description: Turn Hebrew learning material (pasted text, textbook screenshots, lesson transcripts, SMS, word lists) into Anki notes synced with AnkiWeb, deduplicated against the collection, and fix/improve existing Hebrew cards (glosses, IPA, mnemonics, verb links). Use when asked to add Hebrew words to Anki or change Hebrew cards.
---

You are building Anki flashcards for the user's Hebrew study. The user's language is
**Russian by default** — glosses, example translations, mnemonics and chat replies are in
Russian; if the user writes in another language and asks for it, use that language with the
same rules (the gloss field is `$ANKI_HE_GLOSS`). The source may be pasted text, image paths
(textbook pages, screenshots), a lesson transcript, or a plain list of items — usually one
word or set expression per line. Be proactive, and don't hesitate to fix or delete
existing cards. Goal: every useful vocabulary item that is not already in the collection
becomes a note, and the collection gets better each run.

## Tool

Works the same under Claude Code and Codex. No Anki Desktop or Anki-Connect: the
collection is synced with AnkiWeb directly. Code = this skill's directory; data (the
collection, optional backups) = a DATA directory the wrapper picks: `$ANKI_HE_DATA`, else
the git repo around the current directory if it has an `.anki-he` marker, else
`~/.local/share/anki-he`. Credentials: `ANKIWEB_USERNAME`/`ANKIWEB_PASSWORD` from the
environment or `DATA/.env`. Never print them.

`A=<this skill's directory>/anki-he` — the one entry point. Don't write your own
dump/search/sync scripts.
- `$A check` — env sanity; if it fails, stop and report the error.
- `$A pull` — sync from AnkiWeb (two-way, keeps local edits) and dump; with
  `ANKI_HE_BACKUP=1` also a `.colpkg` backup, media mirror and text snapshot in DATA.
- `$A find TERM…` — searches the whole collection. Hebrew TERM matches the nikud-stripped skeleton and the ו/י-stripped
  form across all fields (short words: skeleton on the first field only); `~REGEX` matches
  any field case-insensitively. Pass ALL terms in ONE call.
- `$A show ID…` — full fields of notes.
- `$A sound WORD…` — notes closest by sound to a Russian-letter spelling («мугзам» →
  מֻגְזָם), via IPA similarity. Use it for every Hebrew word that arrives in Cyrillic.
- `$A dups` — exact repeated glosses across the note type.
- `$A apply FILE` — one batch: `{"add":[{fields}], "update":{"<id>":{fields}},
  "delete":[ids]}`; an add item may carry `"tags":[…]`. Re-dumps afterwards.
  Write FILE with a heredoc (no shell-escaping of Hebrew/IPA/Cyrillic), in a temp dir.
- `$A push "MESSAGE"` — sync to AnkiWeb; with backups on and DATA a git repo, also commit
  backups/media/snapshot there and git push (with backups off DATA's git is never touched).
- `$A tool NAME ARGS…` — helpers in `tools/`: `hard_cards [--all] [N] [--json]` (queue of
  notes missing parts of the card standard), `patch_cards PATCH OUT` (compact
  {id: {he, ipa, gloss, ex, tr, hint}} → apply file, keeps the Example layout),
  `check_cards [NID…]` (render cards in headless Chromium, overflow/black-text check),
  `find_dups`, `ipa_normalize`.
- `$A fit` — re-wrap card templates with the auto-fit script (after template changes).

Workflow: `$A check && $A pull` → read the source → `$A find <every candidate, both Hebrew
and ~gloss regexes>` in one command → `show` anything you may update → write one apply
file → `$A apply FILE && $A dups` → `$A push "what changed"` → report, and remind the user
to sync their devices. Be proactive: push without asking for routine add/fix batches; ask
first only for mass rewrites (>~50 existing notes) or anything needing a full sync.

A card sent with no comment (screenshot or its pasted text) means "I can't remember this —
help": bring the note up to the standard below (mnemonic, nikud, example, verb link, precise
gloss), push and report. No clarifying questions. If it already has a 💡 (sent again), that
mnemonic failed — replace it, don't append; re-check the Russian front for ambiguity.

**Voice input.** The user may dictate (speech-to-text). Expect:
- Hebrew words written in Russian letters, often distorted («мугзам», «битуй», «зманим»,
  «лехашкот») → `$A sound` them, take the top hit if its score is ≥ 0.85 or clearly above
  the rest; otherwise try the likely Hebrew spelling with `$A find`.
- Misrecognised Russian («битуй = выражение», «добавь разрушать») — read by sound and intent.
  A bare «добавь X» / «X = Y» with no Hebrew word refers to a card: first the card discussed
  last in the conversation, else the one the user reviewed most recently (`$A pull`, then
  the newest revlog entries); if neither fits, ask one short line naming the candidates.
- Missing punctuation and run-on lists: split into separate items by meaning.

## What makes a card stick

Every Hebrew card should meet this; apply it whenever you touch a card.
1. **One meaning on the front.** The front is what the user must produce; two unrelated
   meanings («обращаться; поворачивать», «ответить / вернуть») make every answer half-wrong.
   Keep the core everyday meaning on the front; a second meaning goes into the hint line
   («второе значение: …») or its own note. Make the front unambiguous in Russian
   («подходить (= годиться)», not «подходить»).
2. **Precise, modern, everyday gloss.** Translate what the word means in real use: «subject to»
   not «согласно» (בְּכָפוּף), «извещение „посылка ждёт“» not «уведомление о получении», add the
   modern sense (תֹּכֶן — «контент»). Register in parentheses: (книжн.), (разг.), (офиц.).
3. **Full nikud, uniform IPA, an example on every card — but the example is NOT what makes
   it stick** — examples rarely help unless they lean on something the user knows very
   well; so build it from surely-known words and a familiar everyday scene (messages from a
   bank or delivery service, shop, doctor, family), keep it short, and never count
   it as the fix for a failing card. The fix is the mnemonic (rule 5).
4. **The vocabulary item, not the document.** From long official phrases keep only the word
   the user needs (שירותים ותכנים פרסומיים → just תֹּכֶן «контент»); base form, masculine
   (פָּשׁוּט לְבִיצּוּעַ, not פְּשׁוּטָה); no separate cards for regular forms — a conjugation table
   becomes one card with the rule in the hint (הָיָה צָרִיךְ).
5. **Mnemonic for every hard card** (lapses ≥ 4, «Again» recently, or the user resent the
   card) — the main tool. One 💡 line about THIS word only. Method = the keyword method
   (Atkinson 1975):

   **Rule: KEYWORD + MEANING DOING SOMETHING TOGETHER, felt in the body, matched on the stress.**

   a) KEYWORD — a concrete, picturable Russian word that sounds like the STRESSED syllable plus
      a neighbour (ле-га-ЛОТ → проГЛОТил; ле-да-ВЕ-ах → даВЕча). Brainstorm ≥ 6 candidates
      (colloquial, slang, old words, brand names, English the user knows); keep the one whose
      sound is closest on the stress. Vowel or one consonant off is OK, two is not.
   b) INTERACTION — keyword and meaning must act on each other in ONE scene, not sit side by
      side: «ГЛОТнул суп и ОБНАРУЖИЛ муху» (the gulp IS the discovery), not «ГЛОТ… обнаружить».
      Research: interactive imagery is what drives the effect; imageability of the scene
      predicts retention more than anything else.
   c) FELT MOMENT — first-person, everyday, sensory: gulp, slip, smell, shout, cat screaming
      at night. Not facts or culture (Колумб, Таглит-as-history), not other people's stories.
      Mild absurdity helps; pure bizarreness fades and is optional.
   d) BOTH DIRECTIONS — cards are tested RU→HE too, and the keyword method alone is weak at
      producing the foreign word. So the Russian gloss on the front must naturally summon the
      scene, and the scene's keyword must carry the Hebrew sound. Test it: read the front
      only — does the scene come? Then from the scene — can you say the Hebrew?
   e) FORMAT — «ле-га-ЛОТ — проГЛОТил ложку супа и ОБНАРУЖИЛ там муху!»: syllables with
      the stressed one in caps, matching Russian sounds in caps, meaning word in caps.
      ≤ 15 words. No explanation of the trick.
   f) ANCHOR instead of keyword only when the anchor word is SURELY known (יוֹתֵר, בָּרוּר,
      זְמַן, מוּכָן, שַׁבָּת, תְּשׁוּבָה) — and even then make it a scene
      («שַׁבָּת посреди недели — никто не работает: ЗАБАСТОВКА»). Long intervals don't prove
      knowledge; if the user says an anchor is unknown, fill that card and set it due today.
   g) REJECT: bare etymology «от X»; loose sound («ДОВЕл» for ДАВЕ); scenes without the meaning
      acting; abstract words in the scene; contrasts («≠ X», «не путать с X», «там…, тут…»).
   h) Binyan meaning as part of the scene when it's the point («хифиль = заставить:
      напои КОТА — לְהַשְׁקוֹת»).
   A resent card = failed mnemonic: throw it away and start from a), don't polish it.
   Bare «от X» hints already in the deck are weak; replace them when those cards turn up
   as hard.
6. **Connectors and function words** (עַל מְנָת, מִפְּנֵי, שְׁאָר, לָכֵן, אֵצֶל, לְהַלָּן) are the
   chronic failures: they have no image — always give them a typical sentence and a vivid
   sound-alike.
7. **Verbs of one root in different binyanim** fail as a group — each gets its own image of
   what the binyan does (cause / self / passive), and verbal nouns link to their verb (←).
8. **Place and proper names: Hebrew → Russian only.** Producing «Кирьят-Моцкин» in Hebrew
   from Russian is pointless; suspend the RU→HE card (template ord 0) of such notes and tag
   them `place` (people's names too, tag `name`). They need nikud but no example.
   Scraps that aren't vocabulary — app/website menu items, song titles, quotes, drill lines
   like «שער - ות», «הייתה - תהיה», a phrase duplicating a word card — get tag `fragment` and
   are suspended. Gender pairs «אַתָּה יָכוֹל… / אַתְּ יְכוֹלָה…» → masculine on the card, feminine in
   the hint.
9. **Short.** Cards must fit a phone screen in a large font; no extra fields, one example,
   one hint line, one verb-link line at most.

`$A tool hard_cards` lists hard notes that still miss parts of this standard —
work through it top-down in batches.

Pasted real-life Hebrew (SMS, letters, ads, chats): ADD the useful new words/meanings right
away — no confirmation needed. Skip ad jargon, names, addresses and other personal data.
If the message looks like phishing, say so in one line.

## Fields (note type `$ANKI_HE_MODEL`, default "Hebrew+IPA+RU")

Always fill the first three:
- "Hebrew" — word/expression with full nikud, e.g. לְהֵירָדֵם
- "IPA transcription" — Modern Israeli IPA, one style for the whole deck:
  - consonants: ʁ resh, x khaf/chet, t͡s tsadi, ʃ shin, ʒ/d͡ʒ/t͡ʃ for ז׳/ג׳/צ׳, j yod, g gimel;
    no ʔ/ʕ (alef/ayin omitted), no h for a silent final ה
  - vowels only a e i o u; diphthongs aj ej oj uj (בין → bejn, לפני → lifˈnej)
  - ˈ before the onset of the stressed syllable (masˈkil, not maskˈil); after a dropped א/ע the
    syllable has no onset, so ˈ follows the closing consonant: lehatˈim, mifˈal, niʁˈe, lidˈog; on every polysyllabic
    word; none on monosyllables; no secondary stress ˌ
  - no brackets, slashes, syllable dots, Latin/Cyrillic transliteration (kh, sh, ts, y)
  - phrases: construct forms as spoken — the first word shortens (שָׁחוֹר → שְׁחוֹר עוֹר ʃxoʁ oʁ,
    xaˈdaʁ ʃeˈna, bejt ˈʃemeʃ); ve/u as pronounced
  → leheʁaˈdem, kaʁˈtis bʁaˈxa, ʁiˈʃon let͡siˈjon
- gloss field (`$ANKI_HE_GLOSS`, default "Русский перевод") — lowercase, meanings comma-separated

"Example" (every card) — огласованное предложение + `<br><span dir=ltr style="color:#999">перевод</span>`,
then optionally the hint line `<br><span dir=ltr style="color:#b58a6a">💡 …</span>` and the
verb-link line (below), in that order.

Verbal nouns (שֵׁם פְּעוּלָה: קְטִילָה / קִטּוּל / הַקְטָלָה / הִתְקַטְּלוּת / הִקָּטְלוּת) get one line
appended to "Example" linking them to their verb:
`<span dir=ltr style="color:#6a8fb5">← לְהַרְשׁוֹת lehaʁˈʃot «разрешать» · хифиль</span>`
(verb with nikud, its IPA — same as on the verb's own note — gloss, binyan)
(binyan in Russian: пааль, пиэль, хифиль, нифаль, хитпаэль). If the verb has no note yet,
add it too (with example). Verbal nouns are learned through their verbs.

Leave any other fields of the note type (e.g. "Notes", "Root+Binyan") EMPTY — long extra
fields don't fit the screen and don't help. Anything worth knowing goes elsewhere:
- register / nuance → a short parenthetical in the gloss: «когда (книжн.)», «ждать (формально)»;
- a related word worth learning (colloquial twin, irregular form) → its own note, after the
  usual duplicate check;
- otherwise drop it.
When you touch an existing note with such fields filled, move the useful bits this way and
clear them.

Tags: `place`, `name`, `fragment` as above; a lesson-date/source tag when it helps to find
the batch later.

## Duplicate check

The collection is the known-word list, and this is where runs go wrong. Collections
often mix ktiv male and ktiv haser (לחסום = לַחְסֹם, לתפוס = לִתְפֹּס), so always search the
Hebrew skeleton AND a Russian-gloss regex — the gloss catches haser twins the short-word
rule misses (חירום vs שְׁעַת חֵרוּם).
- Notes of other note types (older decks, shared decks) may hold the same word without
  nikud or with an English gloss. A word that only exists there is not a duplicate — add
  the proper note.
- If it already exists, skip and report it; if the existing card is worse (no nikud, thin
  gloss, missing example, `/…/` or `[…]` around IPA, filled Notes/Root+Binyan), improve it instead of adding.
- A shared consonantal skeleton is NOT proof of a duplicate — check nikud and binyan:
  לַחְשֹׁב «думать» (пааль) vs לְחַשֵּׁב «вычислять» (пиэль), רָשׁוּם «зарегистрированный»
  vs רִשּׁוּם «регистрация», מַרְצֶה «лектор» vs מְרֻצֶּה «довольный» — all distinct words.

## No two cards may share a Russian gloss

Within this batch and against the collection. When several Hebrew words map to one gloss
(הַדְפָּסָה / הֶדְפֵּס / דְּפוּס → «печать»), give EACH a short parenthetical for the nuance —
process vs. result vs. field: «печать (процесс)», «распечатка, отпечаток», «печать
(полиграфия)». If an existing card collides, fix it too and say so. `$A dups` must come
back empty at the end.

## Normalisation — follow strictly

- Verbs: infinitive (לְ…). Nouns: masculine singular. No separate cards for regular
  feminine/plural/present-tense forms; DO keep irregular plurals (צַד → צְדָדִים) and
  irregular conjugations worth memorising (then name the base verb in the gloss).
- Set expressions and idioms stay intact. Lines with several independent words split into
  separate notes («קדימה אחורה» → קָדִימָה and אֲחוֹרָה).
- NEVER make a preposition-fragment card — a phrase carrying a preposition the source
  sentence happened to put on it. Drop the Hebrew prefix (ב/ל/מ/כ with any fused article),
  the definite article and the Russian preposition, then RECOMPUTE nikud and IPA for the
  lemma: בְּבֵית הֶעָלְמִין «на кладбище» → בֵּית עָלְמִין «кладбище»; מֵהַתַּאֲרִיךְ «с даты»
  → תַּאֲרִיךְ «дата». Keep the preposition only in a set formula (בְּשָׁעָה טוֹבָה), a welded
  adverb (בְּעִיקָּר, בַּחוּץ), the directional ־ָה (אַרְצָה), an inflected preposition
  (עֲבוּרִי), or when the preposition IS the lexeme (בְּמֶשֶׁךְ, בִּשְׁבִיל). Governing
  prepositions (לְחַכּוֹת לְ) only when non-obvious; never both with and without.
- Skip fragments that aren't vocabulary at all («от суммы до», «по семье») and say so.
- No «(м.р.)» / «(ж.р.)» markers — masculine singular is the default.

## Translation quality

- Verify every Hebrew word you produce actually exists. Fix obvious transcript typos
  (נודדי שינה → נְדוּדֵי שֵׁנָה) and report the correction.
- For homonyms, pick the meaning that fits the lesson context (neighbouring lines are
  clues) and flag the choice in one line.

## Output

Just do it and reply in one or two lines: how many cards added/changed, «синхронизируй».
No translations, grammar notes, word lists or mnemonics in the chat — chat text is not
remembered, everything useful goes into the cards. Ask only when an item is
truly ambiguous (which card?), in one short line.
