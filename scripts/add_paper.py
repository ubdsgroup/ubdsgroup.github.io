import sys
import requests
import datetime
import os
import fitz  # PyMuPDF

# CONFIGURATION
# Unpaywall requires an email, but it doesn't verify it. 
# Use your real email or a generic lab one.
UNPAYWALL_EMAIL = "lab_agent@ubdsgroup.io"

def fetch_metadata_and_pdf(identifier):
    print(f"🔍 Searching metadata for: {identifier}...")
    
    # 1. Fetch Metadata from Crossref
    url = f"https://api.crossref.org/{identifier}"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()['message']
    except Exception as e:
        print(f"❌ Error fetching metadata: {e}")
        sys.exit(1)
    
    # Extract basic info
    title = data.get('title', [''])[0]
    # Clean up abstract (remove XML tags often returned by Crossref)
    raw_abstract = data.get('abstract', 'Abstract not available.')
    abstract = raw_abstract.replace('<jats:p>', '').replace('</jats:p>', '').replace('<jats:italic>', '').replace('</jats:italic>', '')
    
    # Format Authors
    author_list = data.get('author', [])
    authors = ", ".join([f"{a.get('given', '')} {a.get('family', '')}" for a in author_list])
    
    # Generate Paper ID (e.g., "Zaidi2021")
    first_author_family = author_list[0].get('family', 'Unknown') if author_list else "Unknown"
    year = data.get('published-print', data.get('issued', {})).get('date-parts', [[None]])[0][0]
    if not year: year = datetime.date.today().year # Fallback
    paper_id = f"{first_author_family}{year}"

    # 2. Attempt PDF Download via Unpaywall
    pdf_path = ""
    pdf_url = ""
    print("📥 Checking for Open Access PDF...")
    
    unpaywall_url = f"https://api.unpaywall.org/{identifier}?email={UNPAYWALL_EMAIL}"
    try:
        u_resp = requests.get(unpaywall_url)
        if u_resp.status_code == 200:
            oa_loc = u_resp.json().get('best_oa_location', {})
            if oa_loc:
                pdf_url = oa_loc.get('url_for_pdf')
    except Exception:
        pass

    if pdf_url:
        print(f"✅ Found PDF: {pdf_url}")
        pdf_dir = "pdfs/papers"
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_filename = f"{paper_id}.pdf"
        pdf_full_path = os.path.join(pdf_dir, pdf_filename)
        
        # Download the file
        pdf_data = requests.get(pdf_url).content
        with open(pdf_full_path, "wb") as f:
            f.write(pdf_data)
        pdf_path = f"/{pdf_dir}/{pdf_filename}" # Path for Jekyll
    else:
        print("⚠️ No Open Access PDF found. Skipping download.")

    # 3. Extract Representative Image
    image_path = ""
    if pdf_path:
        print("🖼️  Hunting for a representative image...")
        image_path = extract_best_image(pdf_full_path, paper_id)

    return {
        "id": paper_id,
        "title": title,
        "authors": authors,
        "journal": data.get('container-title', [''])[0],
        "year": year,
        "doi": identifier,
        "abstract": abstract,
        "pdf": pdf_path,
        "image": image_path,
        "ref": f"{first_author_family} et al., {year}"
    }

def extract_best_image(pdf_file, paper_id):
    """
    Heuristic: Scans the first 5 pages. Extracts the largest image (by area)
    that isn't a tiny icon or logo.
    """
    img_dir = "images/papers"
    os.makedirs(img_dir, exist_ok=True)
    img_filename = f"{paper_id}.png"
    output_path = os.path.join(img_dir, img_filename)
    
    try:
        doc = fitz.open(pdf_file)
        best_image_bytes = None
        max_area = 0
        
        # Scan first 5 pages only (figures are usually early)
        for page_num in range(min(5, len(doc))):
            for img in doc.get_page_images(page_num):
                xref = img[0]
                base_image = doc.extract_image(xref)
                width = base_image["width"]
                height = base_image["height"]
                
                # Filter out small junk (logos, math symbols, lines)
                if width < 200 or height < 200:
                    continue
                
                area = width * height
                if area > max_area:
                    max_area = area
                    best_image_bytes = base_image["image"]
        
        if best_image_bytes:
            with open(output_path, "wb") as f:
                f.write(best_image_bytes)
            print(f"✅ Extracted representative image from PDF.")
            return f"/{img_dir}/{img_filename}"
        else:
            print("⚠️ No suitable images found in PDF.")
            
    except Exception as e:
        print(f"⚠️ Image extraction failed: {e}")
        
    return "" # Return empty if failed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_paper.py <DOI>")
        sys.exit(1)
        
    doi = sys.argv[1]
    paper = fetch_metadata_and_pdf(doi)
    
    # Generate Markdown Content
    content = f"""---
    layout: paper
    title: "{paper['title']}"
    image: {paper['image']}
    pdf: {paper['pdf']}
    ref: {paper['ref']}
    doi: {paper['doi']}
    authors: {paper['authors']}
    journal: {paper['journal']}
    year: {paper['year']}
    ---

    # Abstract
    {paper['abstract']}

    # BibTex
    ```bibtex
        @article{{{paper['id']},
        author="{paper['authors']}",
        year="{paper['year']}",
        journal="{paper['journal']}",
        doi="{paper['doi']}"
        }}
    ```"""

    filename = f"_posts/{datetime.date.today()}-{paper['id']}.md"
    with open(filename, "w") as f:
        f.write(content)
    print(f"🎉 Success! Post created at {filename}")

