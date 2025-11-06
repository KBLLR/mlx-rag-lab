import argparse
from rag.retrieval.vdb import VectorDB
from unstructured.partition.pdf import partition_pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Vector DB from PDF files")
    # Input
    parser.add_argument(
        "--pdfs",
        nargs="+",
        help="The paths to the input PDF files (can be multiple)",
        required=True,
    )
    # Output
    parser.add_argument(
        "--vdb",
        type=str,
        default="models/indexes/combined_vdb.npz",
        help="The path to store the vector DB",
    )
    args = parser.parse_args()

    vdb_instance = VectorDB()
    full_content = []

    for pdf_file in args.pdfs:
        print(f"Processing {pdf_file}...")
        elements = partition_pdf(pdf_file)
        content = "\n\n".join([e.text for e in elements])
        full_content.append(content)
    
    combined_content = "\n\n".join(full_content)
    vdb_instance.ingest(content=combined_content)
    vdb_instance.savez(args.vdb)
    print(f"Vector database created at {args.vdb} from {len(args.pdfs)} PDF(s).")