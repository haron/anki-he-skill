SHELL := /bin/bash
# Skill dirs of the agents that read SKILL.md: Claude Code, Codex, and the shared ~/.agents.
SKILL_DIRS ?= $(HOME)/.claude/skills $(HOME)/.agents/skills $(HOME)/.codex/skills
NAME := hebrew-anki
PY := *.py tools/*.py
# Linters run through uvx with pinned versions: nothing to install except uv (and node).
UVX := uvx -q
RUFF := $(UVX) ruff@0.16.9
PREK := $(UVX) prek@0.5.10
MBAKE := $(UVX) mbake@1.5.0
SHELLCHECK := $(UVX) --from shellcheck-py==0.11.0.1 shellcheck
.PHONY: install uninstall githook linter check clean

# Symlink this checkout into every agent's skill dir (git pull updates it in place).
# A dir that is itself a symlink to another listed dir is skipped by ln -sfn's idempotence.
install:
	@for d in $(SKILL_DIRS); do \
		mkdir -p "$$d" && ln -sfn "$(CURDIR)" "$$d/$(NAME)" && echo "linked $$d/$(NAME)"; \
	done
	./anki-he check || true

uninstall:
	@for d in $(SKILL_DIRS); do \
		if [ -L "$$d/$(NAME)" ]; then rm "$$d/$(NAME)" && echo "removed $$d/$(NAME)"; fi; \
	done

githook:
	$(PREK) install >/dev/null

linter: clean githook
	$(SHELLCHECK) -S warning -x anki-he
	$(RUFF) format $(PY)
	$(RUFF) check --fix $(PY)
	$(RUFF) check $(PY)
	$(MBAKE) validate Makefile
	node --check tools/check_cards.js

# Render cards in headless Chromium: no overflow anywhere, pure black on AnkiDroid.
check:
	./anki-he tool check_cards

clean:
	rm -rf __pycache__ tools/__pycache__ .ruff_cache
