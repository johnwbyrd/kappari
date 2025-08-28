# Kappari: Understanding Paprika 3's API and Database

This project documents how Paprika Recipe Manager 3 works under the hood.  Kappari documents Paprika Recipe Manager's REST API and local SQLite database.

## What is This?

Paprika 3 is a popular recipe management app that stores your recipes both locally (in a SQLite database) and in the cloud (via a REST API). This project reverse-engineered both of these, in order to help developers understand how their own recipe and meal data is stored and synchronized.

Think of this as documentation for accessing your own data programmatically - plus a working Python library.

## Why Would I Care?

If you're a developer who uses Paprika 3, you might want to export your recipes in custom formats, build integrations with other cooking apps, create backup solutions for your recipe collection, analyze your cooking patterns, or understand how modern apps handle data synchronization.

This project provides **documentation and working code**. You can use it to understand the protocols or integrate the library into your own projects.

## Quick Start

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Paprika credentials and database path
   ```

2. **Install for development:**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Run tests:**
   ```bash
   # All tests (requires database + credentials)
   pytest -v
   
   # Core tests only (no external dependencies)
   pytest -v -m "not requires_database and not requires_credentials and not requires_network"
   ```
   
   Tests are marked with `requires_database`, `requires_credentials`, and `requires_network` for selective running.

4. **Code quality:**
   ```bash
   ruff check .      # Lint code
   ruff format .     # Format code
   ```

## Project Structure

The documentation files (`authentication.md`, `crypto.md`, `sqlite.md`, etc.) contain detailed technical information, while `kappari/` has the working Python library that implements the protocols. The `.env.example` file serves as a configuration template.

The Python code is designed to be readable by beginners. It includes plenty of comments and focuses on clarity over cleverness.

## The Technical Bits

### The API (REST)
Paprika 3 uses a REST API (version 2) to sync data between devices. The API requires authentication through email/password login that returns a JWT token. Your app license must be cryptographically verified, and some sensitive information like license details is encrypted using AES-256.

### The Database (SQLite)
Locally, Paprika stores everything in a SQLite database file. This includes your recipes with title, ingredients, directions, photos, and ratings. Categories help organize your recipes with tags. Grocery lists store your shopping lists with checked and unchecked items. Pantry items track your ingredient inventory, and bookmarks save recipe links from websites you've visited.

### The Crypto Stuff
Paprika uses some interesting cryptography to keep your data secure. AES-256-CBC encryption protects license data (think of it as a very secure lock), while RSA signatures prove your license is legitimate. PBKDF2 key derivation turns passwords into encryption keys, and Base64 encoding makes binary data text-friendly.

Don't worry if that sounds complex - the code examples show exactly how it works.

## Legal Reverse Engineering for Interoperability

This project helps you access recipes and data from your own legitimately purchased copy of Paprika 3. It doesn't help you pirate the software, and you should definitely buy Paprika 3 since it's genuinely great software and the developers deserve your support. You need a valid license to use their API anyway.

We created this through [legal reverse engineering for interoperability](https://www.eff.org/issues/coders/reverse-engineering-faq), analyzing network traffic and database files from our own purchased software.

We captured HTTP requests using Fiddler, decompiled the Windows .NET executable with ILSpy and de4dot, analyzed the SQLite database structure, implemented the cryptographic algorithms from scratch, and tested everything with round-trip verification.

The result is clean, documented code that shows exactly how a modern recipe app works behind the scenes.

Paprika Recipe Manager is copyrighted software by Hindsight Labs, LLC.  No affiliation between this project and Hindsight Labs, LLC, is expressed or implied.

## Contributing

Found something we missed? Spotted an error? Contributions welcome! This documentation improves as more developers explore and verify the findings.