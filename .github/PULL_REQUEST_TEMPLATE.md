# Pull Request Template

## Description
Provide a concise summary of the changes introduced by this pull request.

## Related Issues
Closes #{IssueNumber}

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring or performance optimization
- [ ] Test additions or updates

## Verification & Testing
Describe the tests that you ran to verify your changes. Provide instructions so we can reproduce.

### Automated Tests
```bash
# Example:
venv\Scripts\python -m pytest tests/unit/ -v
```

### Manual Verification
Describe any manual testing performed (e.g. verified on localhost:5176 stream rendering).

## Screenshots / Screen Recordings
Add screenshots or video recordings showing the UI changes, console logs, or output results if applicable.

## Checklist
- [ ] My code follows the code style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or console errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] There are no merge conflicts with the target branch
