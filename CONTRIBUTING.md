# Contributing to AI Watermark Remover

Thank you for your interest in contributing to AI Watermark Remover & Background Preserver! We welcome bug reports, documentation updates, feature requests, and code contributions.

---

## 🛠️ Development Setup

1. **Fork & Clone**:
   ```bash
   git clone https://github.com/your-username/image_processor_sandbox.git
   cd image_processor_sandbox
   ```

2. **Environment Setup**:
   - On Windows: Run `setup.bat`
   - On Linux/macOS: Run `./setup.sh`

3. **Verify Environment**:
   ```bash
   python scripts/env_check.py
   ```

4. **Run Local Instance**:
   - On Windows: `Start_AI_Remover.bat`
   - On Linux/macOS: `./start.sh`

---

## 📋 Pull Request Guidelines

- **Zero Hallucination / Single Responsibility**: Keep diffs minimal, clean, and focused on a single issue or feature.
- **Privacy First**: Maintain local-first processing. Do not add external telemetry or cloud upload dependencies without explicit user consent.
- **Linting & Code Quality**: Ensure clean Python code adhering to PEP 8 standards.
- **Documentation**: Update corresponding `docs/` files if your PR introduces new features or changes workflow logic.

---

## 🐛 Reporting Issues

When submitting a bug report, please include:
1. Output of `python scripts/env_check.py`
2. Operating system and GPU/CPU hardware details
3. Steps to reproduce the issue
4. Relevant console error logs

Thank you for helping build privacy-first AI tools!
