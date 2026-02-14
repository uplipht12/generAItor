# Gener(AI)tor

AI-powered wordlist generator for bug bounty reconnaissance. Scrapes a list of target URLs to collect HTTP headers, domains, and endpoints, then leverages Azure OpenAI to extrapolate comprehensive, target-tailored wordlists for brute-force recon.

## How It Works

1. **Scrape** — Reads a file of URLs and makes HTTPS requests to each, collecting response headers, hostnames, and URL paths.
2. **Analyze** — Sends the collected data to Azure OpenAI with a prompt engineered for offensive security reconnaissance.
3. **Generate** — The model produces three wordlists (1,000–5,000 entries each) by expanding on observed patterns:
   - **Headers** — Security headers, cache headers, custom `X-` headers, and variations of observed header names.
   - **Domains** — Subdomains, environment variants (`dev`, `staging`, `api`, `admin`), regional variants, and CDN-specific names.
   - **Endpoints** — API versioning paths, CRUD variations, admin panels, debug endpoints, backup files, and path permutations.

## Installation

```bash
git clone https://github.com/uplipht12/generAItor.git
cd generAItor
pip install -r requirements.txt
```

### Requirements

- Python 3.8+
- An Azure OpenAI resource with a deployed model

## Configuration

Create a `.env` file in the project root with your Azure OpenAI credentials:

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

## Usage

```
python main.py -i <url_file> [-o <output_prefix>]
```

| Flag | Description |
|------|-------------|
| `-i` | **(Required)** Path to a file containing target URLs, one per line. |
| `-o` | Output filename prefix (default: `output`). Files are saved as `<prefix>_headers.txt`, `<prefix>_domains.txt`, and `<prefix>_endpoints.txt`. |
| `-h` | Show help message. |

### Example

```bash
# urls.txt
# https://example.com/api/v1/users
# https://cdn.example.com/assets/main.js
# https://admin.example.com/login

python main.py -i urls.txt -o recon/example
```

Output:

```
[+] Wrote 1523 entries to recon/example_headers.txt
[+] Wrote 2041 entries to recon/example_domains.txt
[+] Wrote 1876 entries to recon/example_endpoints.txt
```

## Limitations

- **Token limits** — Very large URL lists may exceed Azure OpenAI context windows, reducing output quality.
- **Scrape depth** — Currently performs a single `GET` request per URL (no crawling or authenticated scraping).
- **Rate limiting** — No built-in rate limiting or concurrency control; use responsibly.

## Roadmap

- [ ] Waymore integration (`-w` flag) — scrape with Waymore first, then feed results into wordlist generation
- [ ] Selective output (`-m` flag) — generate only `endpoints`, `domains`, `headers`, or `all`
- [ ] Authenticated scraping support
- [ ] Recursive crawling with configurable depth
- [ ] Support for non-Azure OpenAI providers

## License

This project is for authorized security testing only. Use responsibly and only against targets you have permission to test.