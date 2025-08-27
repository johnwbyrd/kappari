# Paprika API v2 Documentation

This project documents our understanding of the Paprika Recipe Manager REST API v2 (used by Paprika 3), and its corresponding sqlite database.  This documentation was created from clean-room reverse engineering of network traffic, the Windows .NET executable, and the sqlite file format.

## Overview

Paprika Recipe Manager is a popular recipe management application available on Windows, Mac, iOS, and Android. This documentation covers API v2 used by Paprika 3, enabling users to access and manage their own recipe data programmatically.

The Windows executable was decompiled with ILSpy, and the resultant source code searched.  The application's sources were apparently obfuscated with an unknown tool, so analysis had to be done functionally.

We document API v2 only. There is an older v1 API that is not covered.

## API Documentation

- [Overview](overview.md) - High-level API summary and conventions
- [Authentication](authentication.md) - Login flow and JWT token management
- [Encoding](encoding.md) - Request/response formats and compression
- [Endpoints](endpoints.md) - Endpoint reference
- [API](api.md) - REST API
- [SQLite](sqlite.md) - Local SQLite cache structure and usage
- [Data Schemas](data-schemas.md) - JSON structure for all entities
- [API Patterns](api-patterns.md) - Common call sequences
- [Cryptographic Implementation](crypto.md) - Detailed encryption/decryption algorithms

## Source Code

The `src/` directory contains Python implementations of the cryptographic algorithms and authentication flows:

- `src/demo_crypto.py` - Demonstration of encryption/decryption process
- `src/paprika_auth.py` - Complete authentication implementation
- Other utility scripts for analysis and debugging

## Legal Notice

Please see our [license](LICENSE.md) covering this documentation and associated software.

This documentation is created through legal clean-room reverse engineering of network traffic from legitimately purchased software for the purpose of interoperability.  We believe that users have the [legal right](https://www.eff.org/issues/coders/reverse-engineering-faq) to access their own data stored in Paprika's cloud service.

Nothing in this documentation permits or enables you to pirate Paprika 3.  Paprika 3 requires a valid license in order to use their online API.  You **should** buy a copy of Paprika 3 as it is a great recipe database with a great design.

## Contributing

This documentation is based on observed API behavior. If you discover additional endpoints or corrections, please contribute your findings.