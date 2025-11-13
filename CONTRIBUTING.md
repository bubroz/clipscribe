# Contributing to ClipScribe

Thank you for your interest in contributing to ClipScribe!

## How to Contribute

**1. Fork & Clone**
```bash
git fork https://github.com/bubroz/clipscribe
cd clipscribe
poetry install
```

**2. Create Branch**
```bash
git checkout -b feature/your-feature-name
```

**3. Make Changes**
- Follow existing code style (Black, type hints)
- Add tests for new features
- Update documentation
- Run tests: `poetry run pytest`

**4. Submit Pull Request**
- Describe what changed and why
- Reference any related issues
- Ensure all tests pass

## Guidelines

**Code Style:**
- Black for formatting: `poetry run black src/`
- Type hints required
- Docstrings for public APIs

**Commit Messages:**
- Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`
- Clear, descriptive messages

**Testing:**
- Add tests for new providers
- Mock external APIs (no real API calls in tests)
- Validate with real audio before PR

**Documentation:**
- Update docs/ for user-facing changes
- Update examples/ if workflow changes
- Keep CHANGELOG.md current

## Adding Providers

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#adding-new-providers) for complete guide.

**Quick overview:**
1. Create provider class in `src/clipscribe/providers/`
2. Implement required interface (TranscriptionProvider or IntelligenceProvider)
3. Register in factory.py
4. Add tests
5. Document in docs/PROVIDERS.md

## Questions?

- Open an issue for bugs or feature requests
- Check [docs/](docs/) for architecture and design docs
- Email: zforristall@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
