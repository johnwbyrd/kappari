# C# Tools for Paprika Analysis

This directory contains C# tools for extracting information from the Paprika executable as decompiled by ILSpy and deobfuscated by de4dot-net8.0.

## StringExtractor.cs

This tool extracts encrypted strings from the Paprika executable by calling the internal string decryption methods. It can extract:

- License encryption keys (indices 53460 and 53414)
- Null check keys (index 34702)
- Public key related strings (indices 16875, 20393, 19815, 16957)

### Usage

1. Update the `paprikaPath` variable in the source code to point to your Paprika executable
2. Compile: `csc StringExtractor.cs`
3. Run: `StringExtractor.exe`

### Output

The tool will output the decrypted string values for the specified indices, which can then be used for:
- Decrypting license data and signatures
- Extracting the RSA public key for signature verification