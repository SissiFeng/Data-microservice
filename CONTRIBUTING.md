# Contributing to Data Microservice

Thank you for considering contributing to the Data Microservice project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Be patient and welcoming
- Be considerate
- Be collaborative
- Be careful in the words you choose
- When we disagree, try to understand why

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue tracker to avoid duplicates. When you create a bug report, include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Describe the behavior you observed and what you expected to see
- Include screenshots if possible
- Include details about your environment (OS, browser, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a clear and descriptive title
- Provide a detailed description of the suggested enhancement
- Explain why this enhancement would be useful
- Include any relevant examples or mockups

### Pull Requests

- Fill in the required template
- Follow the coding style and conventions
- Include appropriate tests
- Update documentation as needed
- End all files with a newline
- Place requires/imports in the following order:
  - Built-in Node modules
  - External modules
  - Internal modules

## Development Setup

### Backend Setup

1. Create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   python run.py
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the development server:
   ```bash
   npm run dev
   ```

## Coding Guidelines

### Python

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions, classes, and modules
- Use meaningful variable and function names
- Keep functions small and focused
- Write unit tests for new functionality

### TypeScript/JavaScript

- Follow the ESLint configuration
- Use TypeScript for type safety
- Use functional components with hooks for React
- Keep components small and focused
- Write unit tests for new functionality

## Git Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Testing

- Write tests for all new features and bug fixes
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

## Documentation

- Update documentation for any changes to APIs, features, or behavior
- Use clear and consistent language
- Include code examples where appropriate

## Questions?

If you have any questions or need help, please open an issue or contact the maintainers.

Thank you for contributing to Data Microservice!
