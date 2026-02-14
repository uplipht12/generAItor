import os
import sys
import socket
import http.client
from urllib.parse import urlparse
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()



def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        usage()
        sys.exit(0)

    input_file, output_prefix = get_arguments()

    make_headers = list()
    make_domains = list()
    make_endpoints = list()

    all_urls = read_url_file(input_file)
    make_scrape_lists(all_urls, make_headers, make_domains, make_endpoints)
    prompt = build_AI_prompt(make_headers, make_domains, make_endpoints)
    result = ai_connect(prompt)
    parse_and_save_wordlists(result, output_prefix)


def get_arguments():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    input_file = None
    output_prefix = "output"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-i" and i + 1 < len(args):
            input_file = args[i + 1]
            i += 2
        elif args[i] == "-o" and i + 1 < len(args):
            output_prefix = args[i + 1]
            i += 2
        else:
            i += 1

    if not input_file:
        print("Error: -i <url_file> is required.")
        usage()
        sys.exit(1)

    return input_file, output_prefix


def read_url_file(filepath):
    """Read URLs from a file, one per line."""
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip()]


def make_scrape_lists(all_urls, make_headers, make_domains, make_endpoints):
    for url in all_urls:
        parsed = urlparse(url)
        # Always collect domain and endpoint even if the request fails
        if parsed.netloc and parsed.netloc not in make_domains:
            make_domains.append(parsed.netloc)
        if parsed.path and parsed.path not in make_endpoints:
            make_endpoints.append(parsed.path)

        try:
            conn = http.client.HTTPSConnection(parsed.netloc, timeout=5)
            conn.request("GET", parsed.path or "/")
            response = conn.getresponse()
            for header in response.getheaders():
                if header not in make_headers:
                    make_headers.append(header)
        except Exception as e:
            print(f"[-] Skipping {url}: {e}")
            continue
        finally:
            try:
                conn.close()
            except Exception:
                pass

def usage():
    print("Usage: python main.py <argument>")
    print("Arguments:")
    print("  -h, --help    Show this help message and exit")
    print("  -i            Input a list of URLs")
    print("  -o            Output the generated wordlists to files (output filename will be appended with _headers.txt, _domains.txt, and _endpoints.txt respectively)")
    print("  -w            Scrape with Waymore first, then use the results to build wordlists for brute-force recon.")
    print("  -m            endpoints, domains, headers, or all")

def build_AI_prompt(make_headers, make_domains, make_endpoints):
    prompt = "You are an expert bug bounty researcher tasked with doing intense and comprehensive reconnaissance on a target program.\n" \
    "Your task is to analyze the following HTTP headers, domains, and endpoints to build comprehensive wordlists for additional brute-force recon.\n" \
    "You should generate three wordlists: one for HTTP headers, one for domains, and one for endpoints.\n\n" \
    "IMPORTANT — Length requirements:\n" \
    "- Each wordlist MUST contain a MINIMUM of 1,000 entries and a MAXIMUM of 5,000 entries.\n" \
    "- Start by including every unique item from the provided data verbatim.\n" \
    "- Then extrapolate aggressively: infer variations, common patterns, naming conventions, permutations, and related terms based on the provided data.\n" \
    "- For headers: include common security headers, cache headers, custom X- headers, and variations of observed header names.\n" \
    "- For domains: include likely subdomains, environment-specific variants (dev, staging, uat, api, admin, internal), regional variants, and CDN/service-specific subdomains.\n" \
    "- For endpoints: include common API versioning paths, CRUD variations, admin panels, debug endpoints, backup file extensions, and path permutations derived from observed patterns.\n" \
    "- Do NOT pad with generic or unrelated filler — every entry should be plausible for the target based on the observed data.\n\n" \
    "OUTPUT FORMAT:\n" \
    "Return exactly three sections, each starting with a header line (=== HEADERS ===, === DOMAINS ===, === ENDPOINTS ===), followed by one entry per line with no numbering, bullets, or extra formatting.\n\n"
    prompt += "HTTP Headers:\n"
    for header in make_headers:
        prompt += f"- {header}\n"
    prompt += "\nDomains:\n"
    for domain in make_domains:
        prompt += f"- {domain}\n"
    prompt += "\nEndpoints:\n"
    for endpoint in make_endpoints:
        prompt += f"- {endpoint}\n"
    
    return prompt

def ai_connect(prompt):
    """Send the prompt to Azure OpenAI and return the generated wordlists."""
    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],   # e.g. https://your-resource.openai.azure.com/
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    )

    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],  # your deployment name in Foundry
        messages=[
            {"role": "system", "content": "You are an expert bug bounty researcher."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


def parse_and_save_wordlists(response_text, output_prefix="output"):
    """Parse the AI response into three wordlists and save each to a separate file."""
    sections = {
        "=== HEADERS ===": "_headers.txt",
        "=== DOMAINS ===": "_domains.txt",
        "=== ENDPOINTS ===": "_endpoints.txt",
    }

    # Ensure parent directory exists
    output_dir = os.path.dirname(output_prefix)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Split response into sections
    current_section = None
    section_lines = {key: [] for key in sections}

    for line in response_text.splitlines():
        stripped = line.strip()
        if stripped in sections:
            current_section = stripped
            continue
        if current_section and stripped:
            section_lines[current_section].append(stripped)

    # Write each section to its file
    for section_marker, suffix in sections.items():
        filepath = output_prefix + suffix
        entries = section_lines[section_marker]
        with open(filepath, "w") as f:
            f.write("\n".join(entries) + "\n")
        print(f"[+] Wrote {len(entries)} entries to {filepath}")


if __name__ == "__main__":
    main()